from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import MessageForm
from .models import Messages
from onboarding.models import User_paths, User_tasks

CustomUser = get_user_model()


def _display_name(user):
    full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return full or user.email


def _load_context(current_user, other_user, ctx_type, ctx_id):
    if not ctx_type or not ctx_id:
        return None, None, None

    if not str(ctx_id).isdigit():
        return None, None, None

    if ctx_type == "task":
        user_task = User_tasks.objects.filter(pk=int(ctx_id)).select_related("user_id", "assigned_by", "task_id").first()
        if not user_task:
            return None, None, None
        participants = {user_task.user_id_id, user_task.assigned_by_id}
        if current_user.id not in participants or other_user.id not in participants:
            return None, None, None
        title = user_task.task_id.title or "Zadanie"
        return "task", user_task, title

    if ctx_type == "path":
        user_path = User_paths.objects.filter(pk=int(ctx_id)).select_related("user", "assigned_by", "path").first()
        if not user_path:
            return None, None, None
        participants = {user_path.user_id, user_path.assigned_by_id}
        if current_user.id not in participants or other_user.id not in participants:
            return None, None, None
        title = user_path.path.name or "Ścieżka"
        return "path", user_path, title

    return None, None, None


def _build_thread_meta(current_user, other_user, context_kind=None, context_obj=None, context_title=None):
    counterpart_name = _display_name(other_user)
    title = counterpart_name
    subtitle = "Rozmowa ogólna"
    query = {}
    if context_kind == "task" and context_obj:
        title = f"{counterpart_name} - Zadanie: {context_title}"
        subtitle = "Czat dotyczący zadania"
        query = {"ctx_type": "task", "ctx_id": context_obj.pk}
    elif context_kind == "path" and context_obj:
        title = f"{counterpart_name} - Ścieżka: {context_title}"
        subtitle = "Czat dotyczący ścieżki"
        query = {"ctx_type": "path", "ctx_id": context_obj.pk}
    return title, subtitle, query


@login_required
def chat_inbox(request, user_id=None):
    current_user = request.user
    query = (request.GET.get("q") or "").strip().lower()
    ctx_type = (request.GET.get("ctx_type") or "").strip().lower()
    ctx_id = (request.GET.get("ctx_id") or "").strip()

    conversation_user_ids = set(Messages.objects.filter(sender=current_user).values_list("receiver_id", flat=True)) | set(
        Messages.objects.filter(receiver=current_user).values_list("sender_id", flat=True)
    )
    conversation_user_ids.discard(current_user.id)

    related_ids = set(current_user.mentees.values_list("id", flat=True))
    if current_user.mentor_id:
        related_ids.add(current_user.mentor_id)
    all_candidate_ids = conversation_user_ids | related_ids

    threads = []
    for other_user in CustomUser.objects.filter(pk__in=all_candidate_ids).exclude(pk=current_user.pk).order_by(
        "first_name", "last_name", "email"
    ):
        title, subtitle, thread_query = _build_thread_meta(current_user, other_user)
        thread_url = f"/chat/{other_user.id}/"
        if thread_query:
            thread_url += f"?{urlencode(thread_query)}"
        threads.append(
            {
                "user": other_user,
                "title": title,
                "subtitle": subtitle,
                "query": thread_query,
                "url": thread_url,
            }
        )

    task_threads = User_tasks.objects.filter(Q(user_id=current_user) | Q(assigned_by=current_user)).select_related(
        "user_id", "assigned_by", "task_id"
    )
    for user_task in task_threads:
        other_user = user_task.assigned_by if user_task.user_id_id == current_user.id else user_task.user_id
        if not other_user:
            continue
        title, subtitle, thread_query = _build_thread_meta(
            current_user,
            other_user,
            context_kind="task",
            context_obj=user_task,
            context_title=user_task.task_id.title,
        )
        threads.append(
            {
                "user": other_user,
                "title": title,
                "subtitle": subtitle,
                "query": thread_query,
                "url": f"/chat/{other_user.id}/?{urlencode(thread_query)}",
            }
        )

    path_threads = User_paths.objects.filter(Q(user=current_user) | Q(assigned_by=current_user)).select_related(
        "user", "assigned_by", "path"
    )
    for user_path in path_threads:
        other_user = user_path.assigned_by if user_path.user_id == current_user.id else user_path.user
        if not other_user:
            continue
        title, subtitle, thread_query = _build_thread_meta(
            current_user,
            other_user,
            context_kind="path",
            context_obj=user_path,
            context_title=user_path.path.name,
        )
        threads.append(
            {
                "user": other_user,
                "title": title,
                "subtitle": subtitle,
                "query": thread_query,
                "url": f"/chat/{other_user.id}/?{urlencode(thread_query)}",
            }
        )

    selected_user = None
    context_kind = None
    context_obj = None
    context_title = None
    if user_id is not None:
        selected_user = get_object_or_404(CustomUser.objects.exclude(pk=current_user.pk), pk=user_id)
        context_kind, context_obj, context_title = _load_context(current_user, selected_user, ctx_type, ctx_id)
    elif threads:
        selected_user = threads[0]["user"]

    if request.method == "POST" and selected_user is not None:
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = current_user
            msg.receiver = selected_user
            if context_kind == "task":
                msg.user_task = context_obj
            elif context_kind == "path":
                msg.user_path = context_obj
            msg.save()
            redirect_params = {}
            if context_kind and context_obj:
                redirect_params = {"ctx_type": context_kind, "ctx_id": context_obj.pk}
            base_url = f"/chat/{selected_user.id}/"
            if redirect_params:
                base_url = f"{base_url}?{urlencode(redirect_params)}"
            return redirect(base_url)
    else:
        form = MessageForm()

    chat_messages = Messages.objects.none()
    if selected_user is not None:
        base_qs = Messages.objects.filter(
            Q(sender=current_user, receiver=selected_user)
            | Q(sender=selected_user, receiver=current_user)
        )
        if context_kind == "task":
            chat_messages = base_qs.filter(user_task=context_obj, user_path__isnull=True).order_by("sent_at")
        elif context_kind == "path":
            chat_messages = base_qs.filter(user_path=context_obj, user_task__isnull=True).order_by("sent_at")
        else:
            chat_messages = base_qs.filter(user_task__isnull=True, user_path__isnull=True).order_by("sent_at")

    selected_query = {}
    if context_kind and context_obj:
        selected_query = {"ctx_type": context_kind, "ctx_id": context_obj.pk}
    selected_url = ""
    selected_chat_title = ""
    selected_chat_subtitle = ""
    if selected_user is not None:
        selected_chat_title, selected_chat_subtitle, _ = _build_thread_meta(
            current_user, selected_user, context_kind, context_obj, context_title
        )
        selected_url = f"/chat/{selected_user.id}/"
        if selected_query:
            selected_url += f"?{urlencode(selected_query)}"

    normalized_threads = []
    seen = set()
    for thread in threads:
        search_blob = f"{thread['title']} {thread['user'].email}".lower()
        if query and query not in search_blob:
            continue
        key = (thread["user"].id, thread["query"].get("ctx_type"), thread["query"].get("ctx_id"))
        if key in seen:
            continue
        seen.add(key)
        thread["is_selected"] = (
            selected_user is not None
            and thread["user"].id == selected_user.id
            and thread["query"].get("ctx_type") == selected_query.get("ctx_type")
            and str(thread["query"].get("ctx_id", "")) == str(selected_query.get("ctx_id", ""))
        )
        normalized_threads.append(thread)

    if selected_user is not None:
        selected_key = (selected_user.id, selected_query.get("ctx_type"), selected_query.get("ctx_id"))
        if selected_key not in seen:
            normalized_threads.append(
                {
                    "user": selected_user,
                    "title": selected_chat_title or _display_name(selected_user),
                    "subtitle": selected_chat_subtitle or "Rozmowa",
                    "query": selected_query,
                    "url": selected_url,
                    "is_selected": True,
                }
            )

    return render(
        request,
        "chat/chat_inbox.html",
        {
            "threads": normalized_threads,
            "selected_user": selected_user,
            "messages": chat_messages,
            "form": form,
            "query": query,
            "selected_querystring": urlencode(selected_query),
            "selected_chat_title": selected_chat_title,
            "selected_chat_subtitle": selected_chat_subtitle,
            "context_kind": context_kind,
            "context_title": context_title,
        },
    )


# Backward-compatible aliases (old URLs/links)
@login_required
def chat_student(request):
    return chat_inbox(request)


@login_required
def chat_mentor(request, student_id=None):
    return chat_inbox(request, user_id=student_id)


@login_required
@require_GET
def chat_updates(request, user_id):
    """Return new messages for current dialog after given last_id."""
    current_user = request.user
    other_user = get_object_or_404(CustomUser.objects.exclude(pk=current_user.pk), pk=user_id)
    ctx_type = (request.GET.get("ctx_type") or "").strip().lower()
    ctx_id = (request.GET.get("ctx_id") or "").strip()
    context_kind, context_obj, _ = _load_context(current_user, other_user, ctx_type, ctx_id)

    last_id_raw = (request.GET.get("last_id") or "").strip()
    last_id = int(last_id_raw) if last_id_raw.isdigit() else 0

    qs = Messages.objects.filter(
        Q(sender=current_user, receiver=other_user)
        | Q(sender=other_user, receiver=current_user)
    )
    if context_kind == "task":
        qs = qs.filter(user_task=context_obj, user_path__isnull=True)
    elif context_kind == "path":
        qs = qs.filter(user_path=context_obj, user_task__isnull=True)
    else:
        qs = qs.filter(user_task__isnull=True, user_path__isnull=True)
    qs = qs.order_by("message_id")
    if last_id > 0:
        qs = qs.filter(message_id__gt=last_id)

    payload = []
    for msg in qs[:100]:
        payload.append(
            {
                "id": msg.message_id,
                "text": msg.text,
                "sender_email": msg.sender.email,
                "sender_label": "Ty" if msg.sender_id == current_user.id else _display_name(msg.sender),
                "sent_at": msg.sent_at.strftime("%d.%m %H:%M"),
            }
        )
    return JsonResponse({"messages": payload})

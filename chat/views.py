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
    query = (request.GET.get("q") or "").strip()
    ctx_type = (request.GET.get("ctx_type") or "").strip().lower()
    ctx_id = (request.GET.get("ctx_id") or "").strip()
    show_mode = (request.GET.get("show") or "recent").strip().lower()
    if show_mode not in ("recent", "all"):
        show_mode = "recent"
    relation_filter = (request.GET.get("relation") or "all").strip().lower()
    if relation_filter not in ("all", "mentor", "mentee", "related", "other"):
        relation_filter = "all"
    sort = (request.GET.get("sort") or "name_asc").strip().lower()
    sort_map = {
        "name_asc": ("first_name", "last_name", "email"),
        "name_desc": ("-first_name", "-last_name", "-email"),
        "email_asc": ("email",),
        "email_desc": ("-email",),
    }
    if sort not in sort_map:
        sort = "name_asc"
    include_task_threads = (request.GET.get("include_tasks") or "1").strip() != "0"
    include_path_threads = (request.GET.get("include_paths") or "1").strip() != "0"
    secondary_user_id_raw = (request.GET.get("s_user_id") or "").strip()
    secondary_ctx_type = (request.GET.get("s_ctx_type") or "").strip().lower()
    secondary_ctx_id = (request.GET.get("s_ctx_id") or "").strip()
    list_query_params = {
        "show": show_mode,
        "relation": relation_filter,
        "sort": sort,
        "include_tasks": "1" if include_task_threads else "0",
        "include_paths": "1" if include_path_threads else "0",
    }
    if query:
        list_query_params["q"] = query
    if secondary_user_id_raw:
        list_query_params["s_user_id"] = secondary_user_id_raw
    if secondary_ctx_type and secondary_ctx_id:
        list_query_params["s_ctx_type"] = secondary_ctx_type
        list_query_params["s_ctx_id"] = secondary_ctx_id
    list_querystring = urlencode(list_query_params)

    conversation_user_ids = set(Messages.objects.filter(sender=current_user).values_list("receiver_id", flat=True)) | set(
        Messages.objects.filter(receiver=current_user).values_list("sender_id", flat=True)
    )
    conversation_user_ids.discard(current_user.id)

    my_mentor_id = current_user.mentor_id
    mentee_ids = set(current_user.mentees.values_list("id", flat=True))
    related_ids = set(mentee_ids)
    if current_user.mentor_id:
        related_ids.add(current_user.mentor_id)

    base_all_users = CustomUser.objects.exclude(pk=current_user.pk)
    if show_mode == "recent" and not query:
        users_qs = CustomUser.objects.filter(pk__in=conversation_user_ids).exclude(pk=current_user.pk)
    else:
        users_qs = base_all_users

    if query:
        users_qs = users_qs.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    if relation_filter == "mentor":
        users_qs = users_qs.filter(pk=my_mentor_id) if my_mentor_id else users_qs.none()
    elif relation_filter == "mentee":
        users_qs = users_qs.filter(pk__in=mentee_ids) if mentee_ids else users_qs.none()
    elif relation_filter == "related":
        users_qs = users_qs.filter(pk__in=related_ids) if related_ids else users_qs.none()
    elif relation_filter == "other":
        users_qs = users_qs.exclude(pk__in=related_ids)

    users_qs = users_qs.order_by(*sort_map[sort])
    threads = []
    for other_user in users_qs:
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
                "kind": "general",
            }
        )

    if include_task_threads:
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
                    "kind": "task",
                }
            )

    if include_path_threads:
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
                    "kind": "path",
                }
            )

    def _resolve_thread(target_user_id, target_ctx_type, target_ctx_id):
        if target_user_id is None:
            return None, None, None, None
        selected = get_object_or_404(CustomUser.objects.exclude(pk=current_user.pk), pk=target_user_id)
        kind, obj, title = _load_context(current_user, selected, target_ctx_type, target_ctx_id)
        selected_query_local = {}
        if kind and obj:
            selected_query_local = {"ctx_type": kind, "ctx_id": obj.pk}
        chat_messages_local = Messages.objects.none()
        base_qs = Messages.objects.filter(
            Q(sender=current_user, receiver=selected)
            | Q(sender=selected, receiver=current_user)
        )
        if kind == "task":
            chat_messages_local = base_qs.filter(user_task=obj, user_path__isnull=True).order_by("sent_at")
        elif kind == "path":
            chat_messages_local = base_qs.filter(user_path=obj, user_task__isnull=True).order_by("sent_at")
        else:
            chat_messages_local = base_qs.filter(user_task__isnull=True, user_path__isnull=True).order_by("sent_at")
        chat_title, chat_subtitle, _ = _build_thread_meta(current_user, selected, kind, obj, title)
        return selected, kind, selected_query_local, {
            "messages": chat_messages_local,
            "chat_title": chat_title,
            "chat_subtitle": chat_subtitle,
        }

    primary_user_id = user_id
    if primary_user_id is None and threads:
        primary_user_id = threads[0]["user"].id

    selected_user, context_kind, selected_query, primary_meta = _resolve_thread(primary_user_id, ctx_type, ctx_id)
    secondary_user = None
    secondary_context_kind = None
    secondary_selected_query = {}
    secondary_meta = {"messages": Messages.objects.none(), "chat_title": "", "chat_subtitle": ""}
    if secondary_user_id_raw.isdigit():
        secondary_user, secondary_context_kind, secondary_selected_query, secondary_meta = _resolve_thread(
            int(secondary_user_id_raw), secondary_ctx_type, secondary_ctx_id
        )

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            target_slot = (request.POST.get("chat_slot") or "primary").strip().lower()
            active_user = selected_user if target_slot != "secondary" else secondary_user
            active_kind = context_kind if target_slot != "secondary" else secondary_context_kind
            active_query = selected_query if target_slot != "secondary" else secondary_selected_query
            if active_user is None:
                return redirect("chat:chat_inbox")
            msg = form.save(commit=False)
            msg.sender = current_user
            msg.receiver = active_user
            if active_kind == "task":
                msg.user_task_id = active_query.get("ctx_id")
            elif active_kind == "path":
                msg.user_path_id = active_query.get("ctx_id")
            msg.save()
            return redirect(request.get_full_path())
    else:
        form = MessageForm()

    normalized_threads = []
    seen = set()
    for thread in threads:
        search_blob = f"{thread['title']} {thread['user'].email}".lower()
        if query and query.lower() not in search_blob:
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
        thread["is_selected_secondary"] = (
            secondary_user is not None
            and thread["user"].id == secondary_user.id
            and thread["query"].get("ctx_type") == secondary_selected_query.get("ctx_type")
            and str(thread["query"].get("ctx_id", "")) == str(secondary_selected_query.get("ctx_id", ""))
        )

        primary_params = {}
        if thread["query"].get("ctx_type") and thread["query"].get("ctx_id"):
            primary_params = {"ctx_type": thread["query"]["ctx_type"], "ctx_id": thread["query"]["ctx_id"]}
        secondary_params = {}
        if secondary_user is not None:
            secondary_params["s_user_id"] = secondary_user.id
            if secondary_selected_query.get("ctx_type") and secondary_selected_query.get("ctx_id"):
                secondary_params["s_ctx_type"] = secondary_selected_query["ctx_type"]
                secondary_params["s_ctx_id"] = secondary_selected_query["ctx_id"]
        primary_open_qs = urlencode({**list_query_params, **secondary_params, **primary_params})

        secondary_open_params = {"s_user_id": thread["user"].id}
        if thread["query"].get("ctx_type") and thread["query"].get("ctx_id"):
            secondary_open_params["s_ctx_type"] = thread["query"]["ctx_type"]
            secondary_open_params["s_ctx_id"] = thread["query"]["ctx_id"]
        if selected_user is not None:
            secondary_open_params["ctx_type"] = selected_query.get("ctx_type", "")
            secondary_open_params["ctx_id"] = selected_query.get("ctx_id", "")
        secondary_open_qs = urlencode(
            {k: v for k, v in {**list_query_params, **secondary_open_params}.items() if v != ""}
        )
        thread["open_primary_url"] = f"/chat/{thread['user'].id}/?{primary_open_qs}"
        thread["open_secondary_url"] = f"/chat/{selected_user.id if selected_user else thread['user'].id}/?{secondary_open_qs}"
        normalized_threads.append(thread)

    close_secondary_url = ""
    if selected_user is not None:
        primary_only_params = {**list_query_params}
        if selected_query.get("ctx_type") and selected_query.get("ctx_id"):
            primary_only_params["ctx_type"] = selected_query["ctx_type"]
            primary_only_params["ctx_id"] = selected_query["ctx_id"]
        close_secondary_url = f"/chat/{selected_user.id}/?{urlencode(primary_only_params)}"

    return render(
        request,
        "chat/chat_inbox.html",
        {
            "threads": normalized_threads,
            "selected_user": selected_user,
            "messages": primary_meta["messages"] if primary_meta else Messages.objects.none(),
            "form": form,
            "query": query,
            "selected_querystring": urlencode(selected_query),
            "selected_chat_title": primary_meta["chat_title"] if primary_meta else "",
            "selected_chat_subtitle": primary_meta["chat_subtitle"] if primary_meta else "",
            "context_kind": context_kind,
            "secondary_selected_user": secondary_user,
            "secondary_messages": secondary_meta["messages"],
            "secondary_selected_querystring": urlencode(secondary_selected_query),
            "secondary_selected_chat_title": secondary_meta["chat_title"],
            "secondary_selected_chat_subtitle": secondary_meta["chat_subtitle"],
            "secondary_context_kind": secondary_context_kind,
            "show_mode": show_mode,
            "relation_filter": relation_filter,
            "sort": sort,
            "include_task_threads": include_task_threads,
            "include_path_threads": include_path_threads,
            "list_querystring": list_querystring,
            "close_secondary_url": close_secondary_url,
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

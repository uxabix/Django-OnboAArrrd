from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import MessageForm
from .models import Messages

CustomUser = get_user_model()


def _display_name(user):
    full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return full or user.email


@login_required
def chat_inbox(request, user_id=None):
    current_user = request.user
    query = (request.GET.get("q") or "").strip()
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

    # Kontakty domyślne: tylko osoby, z którymi użytkownik już pisał.
    conversation_user_ids = set(
        Messages.objects.filter(sender=current_user).values_list("receiver_id", flat=True)
    ) | set(
        Messages.objects.filter(receiver=current_user).values_list("sender_id", flat=True)
    )

    base_all_users = CustomUser.objects.exclude(pk=current_user.pk)

    if show_mode == "recent" and not query:
        contacts = (
            CustomUser.objects.filter(pk__in=conversation_user_ids)
            .exclude(pk=current_user.pk)
        )
    else:
        # Tryb "all" albo aktywne wyszukiwanie.
        contacts = base_all_users

    if query:
        contacts = contacts.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    # Relacja względem bieżącego użytkownika.
    my_mentor_id = current_user.mentor_id
    mentee_ids = set(current_user.mentees.values_list("id", flat=True))
    related_ids = set(mentee_ids)
    if my_mentor_id:
        related_ids.add(my_mentor_id)

    if relation_filter == "mentor":
        contacts = contacts.filter(pk=my_mentor_id) if my_mentor_id else contacts.none()
    elif relation_filter == "mentee":
        contacts = contacts.filter(pk__in=mentee_ids) if mentee_ids else contacts.none()
    elif relation_filter == "related":
        contacts = contacts.filter(pk__in=related_ids) if related_ids else contacts.none()
    elif relation_filter == "other":
        contacts = contacts.exclude(pk__in=related_ids)

    contacts = contacts.order_by(*sort_map[sort])

    selected_user = None
    if user_id is not None:
        selected_user = get_object_or_404(CustomUser.objects.exclude(pk=current_user.pk), pk=user_id)
    elif contacts.exists():
        selected_user = contacts.first()

    # Jeśli wskazany użytkownik nie mieści się w aktualnym filtrze listy (np. podczas
    # wyszukiwania), dopnij go do listy kontaktów, aby dialog był nadal widoczny.
    if selected_user and not contacts.filter(pk=selected_user.pk).exists():
        contacts = (contacts | CustomUser.objects.filter(pk=selected_user.pk)).distinct().order_by(
            *sort_map[sort]
        )

    if request.method == "POST" and selected_user is not None:
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = current_user
            msg.receiver = selected_user
            msg.save()
            return redirect("chat:chat_inbox_user", user_id=selected_user.id)
    else:
        form = MessageForm()

    chat_messages = Messages.objects.none()
    if selected_user is not None:
        chat_messages = Messages.objects.filter(
            Q(sender=current_user, receiver=selected_user)
            | Q(sender=selected_user, receiver=current_user)
        ).order_by("sent_at")

    for contact in contacts:
        if contact.pk == my_mentor_id:
            contact.relation_kind = "mentor"
        elif contact.pk in mentee_ids:
            contact.relation_kind = "mentee"
        else:
            contact.relation_kind = "other"

    list_query_params = {
        "show": show_mode,
        "relation": relation_filter,
        "sort": sort,
    }
    if query:
        list_query_params["q"] = query
    list_querystring = urlencode(list_query_params)

    return render(
        request,
        "chat/chat_inbox.html",
        {
            "contacts": contacts,
            "selected_user": selected_user,
            "messages": chat_messages,
            "form": form,
            "query": query,
            "show_mode": show_mode,
            "relation_filter": relation_filter,
            "sort": sort,
            "list_querystring": list_querystring,
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

    last_id_raw = (request.GET.get("last_id") or "").strip()
    last_id = int(last_id_raw) if last_id_raw.isdigit() else 0

    qs = Messages.objects.filter(
        Q(sender=current_user, receiver=other_user)
        | Q(sender=other_user, receiver=current_user)
    ).order_by("message_id")
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

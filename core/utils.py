def get_limited_top_level_comments(obj, comment_relation: str = "comments", block_limit: int = 20):
    """Возвращает ограниченный список комментариев верхнего уровня,\n    учитывая общее ограничение *block_limit* на количество отображаемых\n    блоков (корневой комментарий + все его ответы).\n
    Параметры:\n    - obj – объект модели, у которого есть связь *comment_relation* (related_name «comments»).\n    - comment_relation – имя связи (related_name) для получения QuerySet'а комментариев.\n    - block_limit – максимальное количество визуальных блоков (корневой + ответы).\n
    Возвращает кортеж: (selected_comments, displayed_blocks, total_root_count).\n    - *selected_comments* – QuerySet/список корневых комментариев для отображения.\n    - *displayed_blocks* – итоговое количество визуальных блоков (root + replies).\n    - *total_root_count* – общее число корневых комментариев у объекта (для расчёта «Показать ещё»).\n    """
    # Получаем менеджер обратной связи (обычно related_name="comments")
    comments_manager = getattr(obj, comment_relation)

    # Все корневые комментарии (parent is null).
    root_qs = (comments_manager.filter(parent__isnull=True)
               .select_related('author')
               .prefetch_related('replies__author')
               .order_by('-created_at'))

    selected = []
    blocks = 0

    for root in root_qs:
        # Подсчитываем ВСЕ ответы на комментарий (включая вложенные уровни),
        # чтобы ограничение *block_limit* учитывало реальное количество
        # визуальных блоков, а не только первый уровень.

        def _count_all_replies(comment):
            """Рекурсивно подсчитывает все ответы (любого уровня) для comment."""
            replies = getattr(comment, 'replies').all()
            total = len(replies)
            for rep in replies:
                total += _count_all_replies(rep)
            return total

        replies_count = _count_all_replies(root)
        need = 1 + replies_count

        # Если добавление этого корневого комментария приведёт к превышению лимита,
        # мы всё-таки показываем его целиком, чтобы пользователь видел связанный
        # диалог. Таким образом, мы гарантируем НЕ МЕНЬШЕ block_limit блоков.
        # (Может получиться чуть больше, но никогда меньше.)

        selected.append(root)
        blocks += need

        if blocks >= block_limit:
            break

    total_root_count = root_qs.count()
    return selected, blocks, total_root_count

def get_total_comments_count(obj):
    """Возвращает общее количество комментариев для объекта *obj*,
    учитывая как корневые комментарии, так и все ответы любого уровня.

    Предполагается, что у объекта есть связь ``related_name='comments'``.
    Если связи нет – возвращается 0.
    """
    manager = getattr(obj, 'comments', None)
    if manager is None:
        return 0

    # ------------------------------------------------------------
    # ВАЖНО! Если к объекту применён `prefetch_related()` с фильтром
    # (например, только `parent__isnull=True`), RelatedManager вернёт
    # КЭШИРОВАННЫЙ набор объектов, из-за чего `.all().count()` покажет
    # лишь часть комментариев (только корневые). Чтобы всегда получать
    # ПОЛНОЕ количество (корневые + ответы), выполняем отдельный COUNT
    # напрямую по модели комментариев, минуя кэш.
    # ------------------------------------------------------------

    try:
        comment_model = manager.model           # модель комментария (например, Comment)
        rel_field_name = manager.field.name     # имя FK ссылающейся модели (post, photo, ...)

        filter_kwargs = {rel_field_name: obj}
        return comment_model.objects.filter(**filter_kwargs).count()
    except Exception:
        # Fallback на старую логику, если структура relation нестандартна
        try:
            return manager.all().count()
        except Exception:
            return 0


def get_unified_cards(objects, card_type, user=None):
    """
    SSOT функция для создания унифицированных карточек.
    Преобразует QuerySet объектов в стандартизированный список словарей.

    Args:
        objects: QuerySet или список объектов моделей.
        card_type: Тип карточки ('news', 'photo', 'growlog', 'store').
        user: Текущий пользователь (для вычисления специфичных данных, например, лайков).

    Returns:
        list: Список словарей с данными для `unified_card.html`.
    """
    cards = []
    for item in objects:
        card_data = {
            'id': item.id,
            'type': card_type,
            'object': item, # Передаем сам объект для гибкости в шаблоне
        }
        cards.append(card_data)
    return cards




def get_sort_asc_desc(model, sort, default):
    order_by = sort[0]
    filed = sort[1:]

    if hasattr(model, filed):
        sort_column = getattr(model, filed)
    else:
        sort_column = default
    if order_by == '+':
        return sort_column.asc()
    else:
        return sort_column.desc()


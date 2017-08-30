from .base import *

# ------------------------------------------------------------------------------
# Select and drop operators
# ------------------------------------------------------------------------------

def selection_context(arg, context):
    if isinstance(arg, Intention):
        arg = arg.evaluate(context)
        if isinstance(arg, pd.Index):
            arg = list(arg)
        if isinstance(arg, pd.Series):
            arg = arg.name
    return arg


def selection_filter(f):
    def wrapper(*args, **kwargs):
        return Intention(lambda x: f(list(x.columns),
                                     *(selection_context(a, x) for a in args),
                                     **{k:selection_context(v, x) for k,v in kwargs.items()}))
    return wrapper


def resolve_selection(df, *args, drop=False):
    if len(args) > 0:
        args = [a for a in flatten(args)]
        ordering = []
        column_indices = np.zeros(df.shape[1])
        for selector in args:
            visible = np.where(selector != 0)[0]
            if not drop:
                column_indices[visible] = selector[visible]
            else:
                column_indices[visible] = selector[visible] * -1
            for selection in np.where(selector == 1)[0]:
                if not df.columns[selection] in ordering:
                    ordering.append(df.columns[selection])
    else:
        ordering = list(df.columns)
        column_indices = np.ones(df.shape[1])
    return ordering, column_indices


@pipe
@group_delegation
@symbolic_evaluation(eval_as_selector=True)
def select(df, *args):
    ordering, column_indices = resolve_selection(df, *args)
    selection = np.where((column_indices == np.max(column_indices)) &
                         (column_indices >= 0))[0]
    df = df.iloc[:, selection]
    ordering = [c for c in ordering if c in df.columns]
    return df[ordering]


@pipe
@group_delegation
@symbolic_evaluation(eval_as_selector=True)
def drop(df, *args):
    _, column_indices = resolve_selection(df, *args, drop=True)
    selection = np.where((column_indices == np.max(column_indices)) &
                         (column_indices >= 0))[0]
    return df.iloc[:, selection]


@selection_filter
def starts_with(columns, prefix):
    return [c for c in columns if c.startswith(prefix)]


@selection_filter
def ends_with(columns, suffix):
    return [c for c in columns if c.endswith(suffix)]


@selection_filter
def contains(columns, substr):
    return [c for c in columns if substr in c]


@selection_filter
def everything(columns):
    return columns


@selection_filter
def num_range(columns, prefix, range):
    colnames = [prefix+str(i) for i in range]
    return [c for c in columns if c in colnames]


@selection_filter
def one_of(columns, specified):
    return [c for c in columns if c in specified]


@selection_filter
def columns_between(columns, start_col, end_col, inclusive=True):
    if isinstance(start_col, str):
        start_col = columns.index(start_col)
    if isinstance(end_col, str):
        end_col = columns.index(end_col)
    return columns[start_col:end_col + int(inclusive)]


@selection_filter
def columns_from(columns, start_col):
    if isinstance(start_col, str):
        start_col = columns.index(start_col)
    return columns[start_col:]


@selection_filter
def columns_to(columns, end_col, inclusive=False):
    if isinstance(end_col, str):
        end_col = columns.index(end_col)
    return columns[:end_col + int(inclusive)]

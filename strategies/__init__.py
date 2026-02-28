# 导出所有版本
from . import v1
from . import v2
from . import v3
from . import v4
from . import v5
from . import v6

AVAILABLE_VERSIONS = {
    'v1': v1,
    'v2': v2,
    'v3': v3,
    'v4': v4,
    'v5': v5,
    'v6': v6,
}
from requre.import_system import ReplaceType
from requre.helpers.requests_response import RequestResponseHandling

MODULE_LIST = [
    ("^requests$", {"who_name": "ogr"}),
    ("^requests$", {"who_name": "gitlab"}),
    ("^requests$", {"who_name": "github"}),
    (
        "^requests$",
        {"who_name": "ogr.services.pagure"},
        {
            "Session.request": [
                ReplaceType.DECORATOR,
                RequestResponseHandling.decorator(item_list=[]),
            ]
        },
    ),
    (
        "^requests$",
        {"who_name": "gitlab"},
        {
            "Session.request": [
                ReplaceType.DECORATOR,
                RequestResponseHandling.decorator(item_list=[]),
            ]
        },
    ),
    (
        "^requests$",
        {"who_name": "github.MainClass"},
        {
            "request": [
                ReplaceType.DECORATOR,
                RequestResponseHandling.decorator(item_list=[]),
            ]
        },
    ),
    (
        "^requests$",
        {"who_name": "github.Requester"},
        {
            "Session.request": [
                ReplaceType.DECORATOR,
                RequestResponseHandling.decorator(item_list=[]),
            ]
        },
    ),
    (
        "^requests$",
        {"who_name": "ogr.services.github_tweak"},
        {
            "request": [
                ReplaceType.DECORATOR,
                RequestResponseHandling.decorator(item_list=[]),
            ]
        },
    ),
]

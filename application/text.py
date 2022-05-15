from application.models import IviApiResponseResult


def generate_ivi_api_link():
    base_link = (
        "https://api.ivi.ru/mobileapi/autocomplete/common/v7/"
        "?query={name}"
        "&limit={limit}"
        "&app_version=870"
        "&object_type=content"
        "&fields="
    )
    return base_link + ",".join(IviApiResponseResult.__fields__.keys())


ivi_api_link = generate_ivi_api_link()

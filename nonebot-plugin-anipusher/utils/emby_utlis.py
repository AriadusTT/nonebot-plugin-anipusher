from ..exceptions import AppError


class EmbyUtils:
    @staticmethod
    def splice_emby_series_url(host: str | None, series_id: str | None, server_id: str | None):
        # 检查参数是否为空
        if not host:
            raise AppError.Exception(AppError.ParamNotFound, "host参数不能为空")
        if not series_id:
            raise AppError.Exception(AppError.ParamNotFound, "id参数不能为空")
        if not server_id:
            raise AppError.Exception(AppError.ParamNotFound, "tag参数不能为空")

        # 检查参数类型
        if not isinstance(host, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的host类型：{type(host)} expected str")
        if not isinstance(series_id, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的series_id类型：{type(series_id)} expected str")
        if not isinstance(server_id, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的server_id类型：{type(server_id)} expected str")

        return f"{host.rstrip('/')}/web/index.html#!/item?id={series_id}&serverId={server_id}"

    @staticmethod  # 拼接Emby图片链接
    def splice_emby_image_url(host: str | None, id: str | int | None, tag: str | None) -> str:
        # 检查参数是否为空
        if not host:
            raise AppError.Exception(AppError.MissingData, "host参数不能为空")
        if not id:
            raise AppError.Exception(AppError.MissingData, "id参数不能为空")
        if not tag:
            raise AppError.Exception(AppError.MissingData, "tag参数不能为空")

        # 检查参数类型
        if not isinstance(host, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的host类型：{type(host)} expected str")
        if not isinstance(id, str | int):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的id类型：{type(id)} expected str or int")
        if not isinstance(tag, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的tag类型：{type(tag)} expected str")

        return f"{host.rstrip('/')}/emby/Items/{str(id)}/Images/Primary?tag={tag}&quality=90"

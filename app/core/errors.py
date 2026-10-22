from fastapi import HTTPException, status


class AppException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundException(AppException):
    pass


class UnauthorizedException(AppException):
    pass


class ForbiddenException(AppException):
    pass


class BadRequestException(AppException):
    pass


class ConflictException(AppException):
    pass


class UnprocessableEntityException(AppException):
    pass


def http_exception_from_app(exc: AppException) -> HTTPException:
    if isinstance(exc, NotFoundException):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, UnauthorizedException):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    if isinstance(exc, ForbiddenException):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, BadRequestException):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, ConflictException):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    if isinstance(exc, UnprocessableEntityException):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message)

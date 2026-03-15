from fastapi import Query


class LimitOffsetParams:
    def __init__(
        self,
        limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
        offset: int = Query(0, ge=0, description="Number of items to skip"),
    ):
        self.limit = limit
        self.offset = offset

from ...database import DatabaseTables


class PushService:
    def __init__(self, source: DatabaseTables.TableName):
        self.source = source

    @classmethod
    async def create_and_run(cls, source: DatabaseTables.TableName):
        instance = cls(source)
        await instance.process()
        return instance

    # 主流程
    async def process(self):
        # 查询数据
        # 数据处理
        # 推送数据
        pass

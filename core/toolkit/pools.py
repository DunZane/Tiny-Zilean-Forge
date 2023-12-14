import datetime

import psycopg2
import yaml
from psycopg2.pool import ThreadedConnectionPool

# 加载配置文件
with open('config/toolkit_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

config_sql = config['settings']['postgresql']


class PostgreSQLConnectionPool:
    _instance = None

    def __init__(self, min_conn=1, max_conn=20, **kwargs):
        if self._instance is None:
            self.pool = ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                **kwargs
            )
            self._instance = self
        else:
            raise Exception("Trying to create a new instance but one already exists")

    @classmethod
    def get_instance(cls, min_conn=1, max_conn=20, **kwargs):
        if cls._instance is None:
            cls._instance = cls(min_conn, max_conn, **kwargs)
        return cls._instance

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, connection):
        self.pool.putconn(connection)

    def close_all(self):
        self.pool.closeall()

    def execute(self, sql, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        self.return_connection(conn)


# 设置连接池为模块的变量
pool = PostgreSQLConnectionPool(
    min_conn=config_sql['minconn'],
    max_conn=config_sql['maxconn'],
    database=config_sql['database'],
    user=config_sql['user'],
    password=config_sql['password'],
    host=config_sql['host'],
    port=config_sql['port']
)


def perform_insert(data, metric):
    # 基本的数据处理
    drift_label, drift_start, drift_end = data[0], data[1][0], data[1][1]
    drift_start = drift_start.strftime('%Y-%m-%d %H:%M:%S')
    drift_end = drift_end.strftime('%Y-%m-%d %H:%M:%S')

    # 确定sql语句
    if metric in ['cpu', 'mem', 'processes']:
        sql = f'INSERT INTO {metric} (drift_label, drift_start, drift_end) VALUES (%s, %s, %s)'
    else:
        raise Exception(f"This {metric} type is not currently supported.")
    # 执行参数
    params = (drift_label, drift_start, drift_end)

    # 从连接池中获取连接
    conn = pool.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            print("Data successfully inserted into the database.")
    except (psycopg2.DatabaseError, psycopg2.OperationalError) as e:
        print(f"Error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        conn.rollback()
    finally:
        pool.return_connection(conn)
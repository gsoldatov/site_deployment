from psycopg2.extensions import AsIs


class BaseLogger:
    """ Abstract logger. """
    def log(self, **kwargs):
        raise NotImplementedError
    
    def flush(self):
        raise NotImplementedError


class PrintLogger(BaseLogger):
    """ Logger, which prints to stdout. """
    def log(self, **kwargs):
        print(kwargs["message"])
    
    def flush(self):
        pass


class DatabaseLogger(BaseLogger):
    """ Logger, which saves records to the `fetch_jobs_logs` table in the database. """
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.records = []
    
    def log(self, **kwargs):
        self.records.append((kwargs["record_time"], kwargs["execution_id"], kwargs["job_name"], 
            kwargs["level"], kwargs["message"]))
    
    def flush(self):
        if len(self.records) == 0: return

        with self.db_connection:
            with self.db_connection.cursor() as cursor:
                query = "INSERT INTO fetch_jobs_logs (record_id, record_time, execution_id, job_name, level, message) VALUES " + \
                    ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(self.records))))
                params = []
                for record in self.records: 
                    params.append(AsIs("DEFAULT"))
                    params.extend(record)
                cursor.execute(query, params)
        
        self.records = []

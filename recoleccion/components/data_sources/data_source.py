import logging


class DataSource:
    """
    Representes a resource of a DataSource
    It has:
    - name: the name of the resource
    - key: the key of the resource (used to uniquely identify it)
    """

    name = None
    key = None
    column_mappings = {}
    logger = logging.getLogger(__name__)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"({self.name}, {self.key})"

    def clean_data(self, data):
        """
        Clean the data of the resource
        """
        raise NotImplementedError

    @classmethod
    def get_and_rename_relevant_columns(cls, data):
        """
        Get the relevant columns of the data as a DataFrame and rename them
        """
        data.columns = [column.lower() for column in data.columns]
        correct_columns = list(getattr(cls, "correct_columns", set()))
        relevant_column_names = [key.lower() for key in cls.column_mappings.keys()] + correct_columns
        existing_columns = [column for column in relevant_column_names if column in data.columns]
        relevant_columns = data[existing_columns]
        renamed = relevant_columns.rename(columns=cls.column_mappings)
        return renamed

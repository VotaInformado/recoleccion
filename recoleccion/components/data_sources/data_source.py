from recoleccion.utils.custom_logger import CustomLogger


class Resource:
    """
    Representes a resource of a DataSource
    It has:
    - name: the name of the resource
    - key: the key of the resource (used to uniquely identify it)
    """

    name = None
    key = None
    column_mappings = {}

    def __init__(self):
        self.logger = CustomLogger()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"({self.name}, {self.key})"

    def clean_data(self, data):
        """
        Clean the data of the resource
        """
        raise NotImplementedError

    def get_and_rename_relevant_columns(self, data):
        """
        Get the relevant columns of the data as a DataFrame and rename them
        """
        data.columns = [column.lower() for column in data.columns]
        correct_columns = list(getattr(self, "correct_columns", set()))
        relevant_column_names = [key.lower() for key in self.column_mappings.keys()] + correct_columns
        relevant_columns = data[relevant_column_names]
        correct_columns = getattr(self, "correct_columns", set())
        renamed = relevant_columns.rename(columns=self.column_mappings)
        return renamed


class DataSource:
    base_url = None
    resources = []

    def get_resources(self):
        return self.resources

    def get_resource(self, resource):
        """
        Recieves a Resource object and returns it as a DataFrame
        """
        raise NotImplementedError

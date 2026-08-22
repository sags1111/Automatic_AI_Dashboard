import json


class JSONConverter:

    @staticmethod
    def save(schema, output_file):
        """
        Save the extracted schema as a JSON file.
        """

        with open(output_file, "w") as file:
            json.dump(schema, file, indent=4)

        print(f"Schema saved to {output_file}")
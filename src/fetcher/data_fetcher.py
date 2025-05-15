import json
from bson import json_util
from utils.eda import clean_mongo_data, clean_postgres_data, add_engineer_data_to_combined_data, attach_job_actions_to_engineers

class DataFetcher:
    def __init__(self, mongo_conn, pg_conn, json_manager):
        self.mongo_conn = mongo_conn
        self.pg_conn = pg_conn
        self.json_manager = json_manager
        self.combined_data = []
        self.job_interactions = []
        self.job_actions = []

    def fetch_and_save_mongo(self, collection_name):
        """
        Fetch data from a MongoDB collection, clean it, and save to JSON.
        """
        try:
            raw_data = self.mongo_conn.fetch_all(collection_name)
            if raw_data:
                # Parse raw JSON string and clean data
                data = json.loads(raw_data, object_hook=json_util.object_hook)
                print(f"Raw {collection_name} data: {len(data)} records")
                cleaned_data = clean_mongo_data(data)
                print(f"Cleaned {collection_name} data: {len(cleaned_data)} records")
                # Save cleaned data to JSON
                self.json_manager.write_json(collection_name, cleaned_data)
                print(f"Data written to data\\{collection_name}.json")
                # Store projects data for combining
                if collection_name == "projects":
                    self.combined_data = cleaned_data
            else:
                print(f"No data found in MongoDB collection: {collection_name}")
        except Exception as e:
            print(f"Error fetching or saving MongoDB data for {collection_name}: {e}")

    def fetch_and_save_postgres(self, table_name):
        """
        Fetch data from a PostgreSQL table, clean it, and save to JSON.
        """
        try:
            data = self.pg_conn.fetch_all(table_name)
            if data:
                # Clean data
                print(f"Raw {table_name} data: {len(data)} records")
                cleaned_data = clean_postgres_data(data, table_name)
                print(f"Cleaned {table_name} data: {len(cleaned_data)} records")
                # Save cleaned data to JSON
                self.json_manager.write_json(table_name, cleaned_data)
                print(f"Data written to data\\{table_name}.json")
                # Store for combining
                if table_name == "job_interactions":
                    self.job_interactions = cleaned_data
                elif table_name == "job_actions":
                    self.job_actions = cleaned_data
            else:
                print(f"No data found in PostgreSQL table: {table_name}")
        except Exception as e:
            print(f"Error fetching or saving PostgreSQL data for {table_name}: {e}")

    def combine_and_save_data(self):
        """
        Combine projects, job_interactions, and job_actions into combined_data.json.
        """
        try:
            if not self.combined_data:
                print("No projects data available for combining.")
                return
            
            # Create a copy to avoid modifying cached data
            combined_data = self.combined_data.copy()
            
            # Add engineer data
            if self.job_interactions:
                print(f"Adding {len(self.job_interactions)} job_interactions to projects")
                combined_data = add_engineer_data_to_combined_data(combined_data, self.job_interactions)
            
            # Attach job actions
            if self.job_actions:
                print(f"Attaching {len(self.job_actions)} job_actions to engineers")
                combined_data = attach_job_actions_to_engineers(combined_data, self.job_actions)
            
            # Save combined data
            self.json_manager.write_json("combined_data", combined_data)
            print("Data written to data\\combined_data.json")
        except Exception as e:
            print(f"Error combining and saving data: {e}")

    def update_combined_data_for_project(self, project, operation):
        """
        Update combined_data.json for a project change (INSERT, UPDATE, DELETE).
        """
        try:
            combined_data = self.json_manager.load_json("combined_data")
            if not isinstance(combined_data, list):
                combined_data = [combined_data] if combined_data else []
            
            project_id = project.get("_id") if operation != "DELETE" else project.get("_id")
            
            if operation == "INSERT" or operation == "UPDATE":
                # Clean project data
                cleaned_project = clean_mongo_data(project.copy())
                # Find related job_interactions
                related_interactions = [ji for ji in self.job_interactions if str(ji.get("unique_project_id")) == str(cleaned_project.get("project_id"))]
                # Add engineers
                cleaned_project = add_engineer_data_to_combined_data([cleaned_project], related_interactions)[0]
                # Attach job actions
                cleaned_project = attach_job_actions_to_engineers([cleaned_project], self.job_actions)[0]
                # Update or insert project
                for i, item in enumerate(combined_data):
                    if item.get("_id") == project_id:
                        combined_data[i] = cleaned_project
                        break
                else:
                    combined_data.append(cleaned_project)
            elif operation == "DELETE":
                combined_data = [item for item in combined_data if item.get("_id") != project_id]
            
            self.json_manager.write_json("combined_data", combined_data)
            print(f"Updated combined_data.json for project {project_id}: {operation}")
        except Exception as e:
            print(f"Error updating combined_data for project: {e}")

    def update_combined_data_for_interaction(self, interaction, operation, record_id):
        """
        Update combined_data.json for a job_interaction change.
        """
        try:
            combined_data = self.json_manager.load_json("combined_data")
            if not isinstance(combined_data, list):
                combined_data = [combined_data] if combined_data else []
            
            unique_project_id = interaction.get("unique_project_id") if operation != "DELETE" else None
            
            if operation == "INSERT" or operation == "UPDATE":
                cleaned_interaction = clean_postgres_data(interaction.copy(), "job_interactions")
                for project in combined_data:
                    if str(project.get("project_id")) == str(unique_project_id):
                        project.setdefault("engineers", [])
                        # Update or insert engineer
                        for i, eng in enumerate(project["engineers"]):
                            if eng.get("id") == cleaned_interaction.get("id"):
                                project["engineers"][i] = cleaned_interaction
                                break
                        else:
                            project["engineers"].append(cleaned_interaction)
                        # Attach job actions
                        related_actions = [ja for ja in self.job_actions if str(ja.get("job_interaction_id")) == str(cleaned_interaction.get("id"))]
                        project = attach_job_actions_to_engineers([project], related_actions)[0]
            elif operation == "DELETE":
                for project in combined_data:
                    if project.get("engineers"):
                        project["engineers"] = [eng for eng in project["engineers"] if eng.get("id") != record_id]
            
            self.json_manager.write_json("combined_data", combined_data)
            print(f"Updated combined_data.json for job_interaction {record_id}: {operation}")
        except Exception as e:
            print(f"Error updating combined_data for job_interaction: {e}")

    def update_combined_data_for_action(self, action, operation, record_id):
        """
        Update combined_data.json for a job_action change.
        """
        try:
            combined_data = self.json_manager.load_json("combined_data")
            if not isinstance(combined_data, list):
                combined_data = [combined_data] if combined_data else []
            
            job_interaction_id = action.get("job_interaction_id") if operation != "DELETE" else None
            
            if operation == "INSERT" or operation == "UPDATE":
                cleaned_action = clean_postgres_data(action.copy(), "job_actions")
                for project in combined_data:
                    for engineer in project.get("engineers", []):
                        if str(engineer.get("id")) == str(job_interaction_id):
                            engineer.setdefault("job_actions", [])
                            # Update or insert action
                            for i, act in enumerate(engineer["job_actions"]):
                                if act.get("id") == cleaned_action.get("id"):
                                    engineer["job_actions"][i] = cleaned_action
                                    break
                            else:
                                engineer["job_actions"].append(cleaned_action)
                            break
            elif operation == "DELETE":
                for project in combined_data:
                    for engineer in project.get("engineers", []):
                        if engineer.get("job_actions"):
                            engineer["job_actions"] = [act for act in engineer["job_actions"] if act.get("id") != record_id]
            
            self.json_manager.write_json("combined_data", combined_data)
            print(f"Updated combined_data.json for job_action {record_id}: {operation}")
        except Exception as e:
            print(f"Error updating combined_data for job_action: {e}")
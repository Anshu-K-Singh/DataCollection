# src/utils/eda.py
keys_to_remove = [
    "tools_used", "system_provided", "__v", "rand_no", "cron_date",
    "post_to_career_page", "sort_order", "sort_order_date", "dummy_no_requirements",
    "is_screening_question_added", "overall_pass_percent", "screening_question_add_date",
    "screening_question_added_by", "communication_skill", "screening_question_updated_by",
    "ai_interviewer", "locations", "ai_interviewer_template_id", "edit_logs",
    "documents", "bgv", "asset_system", "ist_time_zone_end_time", "ist_time_zone_start_time",
    "pf_details", "previous_pf_required", "technical_assesment", "interview_rounds",
    "max_experience", "min_experience", "working_hours", "mark_as_active",
    "mark_as_active_date", "experience_level", "preffered_location", "education_type",
    "hiring_manager", "contact_person", "tags", "interview_rounds_ats",
    "cooling_period_department", "cooling_period_location", "internship_duration",
    "project_duration", "reason_for_job_close", "reason_for_job_paused", "vendor_details",
    "vendor_admin", "auto_lost", "job_status_logs", "lost_reason", "status",
    "linkedin_job_title", "department", "is_world_wide", "offer_sent_count",
    "offer_reject_count", "show_in_jd", "is_client_deleted", "whatsapp_notification_sent",
    "project_logs", "is_ai_apply", "is_it_sow_sate"
]

interaction_keys_to_remove = [
    "project_id", "client_name", "reason_for_rejection", "final_price",
    "created_at", "updated_at", "job_experience", "source", "job_location",
    "engineer_experience_months", "engineer_profile_pic", "project_requirements",
    "job_status", "offer_status", "am_assigned", "account_manager_id",
    "platform_type", "offer_remarks", "offer_docx_url", "pool_status",
    "pool_comment", "pool_date", "is_delete", "company_id", "linkedin_job_title",
    "client_lead_type", "is_onboarded", "hiring_type", "is_it_sow_sate",
    "is_ai_apply", "client_id", "negotiation", "cover_letter",
    "engineer_communication", "engineer_test_result", "engineer_test_score",
    "engineer_status", "notice_period_confirmed_id", "notice_period_confirmed_name",
    "release_category_id", "release_category_name", "release_category_remark",
    "hr_negotiation", "developer_showed_interest", "tenant_id", "reason_for_dropping",
    "offer_docx_details", "verification_comment", "doc_url", "skill_vetting",
    "ss_verified", "ss_verified_by", "ss_verified_at", "ss_verified_comment",
    "ss_verified_doc_url", "ss_verified_doc_url_name", "ss_verified_doc_url_type",
    "ss_verified_doc_url_type_name", "ss_verified_doc_url_type_remark",
    "ss_verified_doc_url_type_remark_name", "ss_verified_doc_url_type_remark_id",
    "ss_verified_doc_url_type_remark_id_name", "hr_background",
    "is_permanent_rejected", "interview_status", "is_vendor_developer",
    "vendor_id", "is_applied_on_vendor_job", "screening_pass_status",
    "screening_percent", "ai_interview_link_open_at", "email_before_ai_interview",
    "user_pic_ai_interview", "ai_interview_start_at", "negotiated_price",
    "revised_notice_period", "additional_price", "ai_interview_template_id",
    "ai_interview_id", "ai_interview_status", "is_show_client", "is_show_ss_price",
    "is_existing", "dev_id", "sort_order", "sort_order_date", "in_hand_offer",
    "offer_details", "additional_info"
]

action_keys_to_remove = [
    "job_interview_id", "updated_at", "action_by_role", "comment",
    "owner_action_by_id", "sales_poc_id", "department_id", "id",
    "action_by_id", "platform_type", "project_id", "lead_type"
]

def clean_mongo_data(data):
    """
    Clean MongoDB data by removing specified keys and simplifying nested fields.
    """
    if isinstance(data, dict):
        # Remove specified keys
        for key in keys_to_remove:
            data.pop(key, None)
        
        # Simplify nested fields
        if "primary_skills" in data and isinstance(data["primary_skills"], list):
            skills = [skill.get("skill") for skill in data["primary_skills"] if isinstance(skill, dict)]
            data["primary_skills"] = list(filter(None, skills))
        
        if "secondary_skills" in data and isinstance(data["secondary_skills"], list):
            skills = [skill.get("skill") for skill in data["secondary_skills"] if isinstance(skill, dict)]
            data["secondary_skills"] = list(filter(None, skills))
        
        if "travel_preference" in data and isinstance(data["travel_preference"], list):
            for entry in data["travel_preference"]:
                if isinstance(entry, dict) and "data" in entry:
                    data["travel_preference"] = entry["data"]
                    break
            else:
                data["travel_preference"] = ""
        
        if "month_of_engagement" in data and isinstance(data["month_of_engagement"], list):
            for entry in data["month_of_engagement"]:
                if isinstance(entry, dict) and "data" in entry:
                    data["month_of_engagement"] = entry["data"]
                    break
            else:
                data["month_of_engagement"] = ""
        
        if "working_time_zone" in data and isinstance(data["working_time_zone"], list):
            for entry in data["working_time_zone"]:
                if isinstance(entry, dict) and "label" in entry:
                    data["working_time_zone"] = entry["label"]
                    break
            else:
                data["working_time_zone"] = ""
        
        if "role" in data and isinstance(data["role"], list):
            for entry in data["role"]:
                if isinstance(entry, dict) and "role" in entry:
                    data["role"] = entry["role"]
                    break
            else:
                data["role"] = ""
        
        if "experience_range" in data and isinstance(data["experience_range"], list):
            for entry in data["experience_range"]:
                if isinstance(entry, dict) and "data" in entry:
                    data["experience_range"] = entry["data"]
                    break
            else:
                data["experience_range"] = ""
        
        if "hiring_type" in data and isinstance(data["hiring_type"], list):
            for entry in data["hiring_type"]:
                if isinstance(entry, dict) and "data" in entry:
                    data["hiring_type"] = entry["data"]
                    break
            else:
                data["hiring_type"] = ""
        
        if "engagement_type" in data and isinstance(data["engagement_type"], list):
            for entry in data["engagement_type"]:
                if isinstance(entry, dict) and "data" in entry:
                    data["engagement_type"] = entry["data"]
                    break
            else:
                data["engagement_type"] = ""
        
        if "tentative_start" in data and isinstance(data["tentative_start"], list):
            for entry in data["tentative_start"]:
                if isinstance(entry, dict) and "data" in entry:
                    data["tentative_start"] = entry["data"]
                    break
            else:
                data["tentative_start"] = ""
        
        if "talent_manager_associate" in data and isinstance(data["talent_manager_associate"], list):
            first_entry = data["talent_manager_associate"][0] if data["talent_manager_associate"] else {}
            if isinstance(first_entry, dict):
                first_name = first_entry.get("first_name", "").strip()
                last_name = first_entry.get("last_name", "").strip()
                full_name = f"{first_name} {last_name}".strip()
                data["talent_manager_associate"] = full_name if full_name else ""
            else:
                data["talent_manager_associate"] = ""
        
        if "sales_poc" in data and isinstance(data["sales_poc"], list):
            first_entry = data["sales_poc"][0] if data["sales_poc"] else {}
            if isinstance(first_entry, dict):
                first_name = first_entry.get("first_name", "").strip()
                last_name = first_entry.get("last_name", "").strip()
                full_name = f"{first_name} {last_name}".strip()
                data["sales_poc"] = full_name if full_name else ""
            else:
                data["sales_poc"] = ""
        
        if "client_poc" in data and isinstance(data["client_poc"], list):
            client_poc_entry = data["client_poc"][0] if data["client_poc"] else {}
            data["client_point_of_contact_email"] = client_poc_entry.get("email", "")
            data["client_point_of_contact_mobile"] = client_poc_entry.get("mobile_number", "")
            data["client_point_of_contact_name"] = client_poc_entry.get("client_poc", "")
            data["client_point_of_contact_designation"] = client_poc_entry.get("designation", "")
            del data["client_poc"]
    
    elif isinstance(data, list):
        for item in data:
            clean_mongo_data(item)
    
    return data

def clean_postgres_data(data, table_name):
    """
    Clean PostgreSQL data by removing specified keys and simplifying fields.
    """
    keys_to_remove = interaction_keys_to_remove if table_name == "job_interactions" else action_keys_to_remove
    
    if isinstance(data, dict):
        # Remove specified keys
        for key in keys_to_remove:
            data.pop(key, None)
        
        # Simplify skills fields (if present)
        if "job_primary_skills" in data and isinstance(data["job_primary_skills"], list):
            data["job_primary_skills"] = [skill["skill"] for skill in data["job_primary_skills"] if isinstance(skill, dict) and "skill" in skill]
        
        if "engineer_primary_skill" in data and isinstance(data["engineer_primary_skill"], list):
            data["engineer_primary_skill"] = [skill["skill_name"] for skill in data["engineer_primary_skill"] if isinstance(skill, dict) and "skill_name" in skill]
    
    elif isinstance(data, list):
        for item in data:
            clean_postgres_data(item, table_name)
    
    return data

def add_engineer_data_to_combined_data(cleaned_projects, job_interactions):
    """
    Add engineer data from job_interactions to projects data.
    """
    for job_entry in job_interactions:
        unique_project_id = job_entry.get("unique_project_id")
        if not unique_project_id:
            continue

        for project_entry in cleaned_projects:
            if str(project_entry.get("project_id")) == str(unique_project_id):
                project_entry.setdefault("engineers", [])
                engineer_data = {
                    "id": job_entry.get("id"),
                    "engineer_name": job_entry.get("engineer_name"),
                    "status": job_entry.get("status"),
                    "quoted_price": job_entry.get("quoted_price"),
                    "engineer_role": job_entry.get("engineer_role"),
                    "contract_type": job_entry.get("contract_type"),
                    "engineer_experience_years": job_entry.get("engineer_experience_years"),
                    "total_interview_rounds": job_entry.get("total_interview_rounds"),
                    "project_duration": job_entry.get("project_duration"),
                    "engineer_primary_skill": job_entry.get("engineer_primary_skill"),
                    "contract_start_date": job_entry.get("contract_start_date"),
                    "contract_end_date": job_entry.get("contract_end_date"),
                    "engineer_email": job_entry.get("engineer_email"),
                    "account_manager_name": job_entry.get("account_manager_name"),
                    "resume": job_entry.get("resume"),
                    "lead_type": job_entry.get("lead_type"),
                    "company": job_entry.get("company"),
                    "developer_type": job_entry.get("developer_type"),
                    "client_city": job_entry.get("client_city"),
                    "client_state": job_entry.get("client_state"),
                    "client_country": job_entry.get("client_country"),
                    "client_industry_type": job_entry.get("client_industry_type"),
                    "onboarding_date": job_entry.get("onboarding_date"),
                    "engineer_mobile": job_entry.get("engineer_mobile"),
                    "web_app_platform": job_entry.get("web_app_platform"),
                    "billing_date": job_entry.get("billing_date"),
                    "am_assign_poc": job_entry.get("am_assign_poc"),
                    "developer_cost": job_entry.get("developer_cost")
                }
                project_entry["engineers"].append(engineer_data)
    
    return cleaned_projects

def attach_job_actions_to_engineers(cleaned_projects, job_actions):
    """
    Attach job actions to engineers in the projects data.
    """
    try:
        # Group actions by job_interaction_id
        actions_by_id = {}
        for action in job_actions:
            job_id = str(action.get("job_interaction_id"))
            actions_by_id.setdefault(job_id, []).append(action)

        # Add matching actions to engineers
        for project in cleaned_projects:
            for engineer in project.get("engineers", []):
                eng_id = str(engineer.get("id"))
                engineer["job_actions"] = actions_by_id.get(eng_id, [])
        
        print("Job actions attached to engineers.")
        return cleaned_projects
    except Exception as e:
        print(f"Error attaching job actions: {e}")
        return cleaned_projects
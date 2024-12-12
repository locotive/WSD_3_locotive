from typing import Dict, List, Optional

def validate_job_data(data: Dict) -> Optional[str]:
    """
    Validate job posting data
    Returns error message if validation fails, None if successful
    """
    required_fields = ['title', 'job_description', 'company_id']
    
    if not all(field in data for field in required_fields):
        return "Missing required fields"

    if 'location' in data:
        if not isinstance(data['location'], dict) or 'city' not in data['location']:
            return "Invalid location format"

    if 'tech_stacks' in data and not isinstance(data['tech_stacks'], list):
        return "tech_stacks must be a list"

    if 'job_categories' in data and not isinstance(data['job_categories'], list):
        return "job_categories must be a list"

    return None

def prepare_job_filters(args: Dict) -> Dict:
    """
    Prepare filters from request arguments
    """
    filters = {}
    
    # Text search filters
    for field in ['keyword', 'company', 'employment_type', 'position', 'salary_info', 'experience_level']:
        if args.get(field):
            filters[field] = args[field]

    # ID filters
    if args.get('location_id'):
        try:
            filters['location_id'] = int(args['location_id'])
        except ValueError:
            pass

    # List filters
    for field in ['tech_stacks', 'job_categories']:
        if args.getlist(field):
            filters[field] = args.getlist(field)

    # Sorting
    filters['sort_field'] = args.get('sort_field', 'created_at')
    filters['sort_order'] = args.get('sort_order', 'desc')

    return filters 
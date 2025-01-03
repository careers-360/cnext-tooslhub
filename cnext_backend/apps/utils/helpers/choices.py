from tools.models import CasteCategory, DisabilityCategory

CONSUMPTION_TYPE = {"paid": "Paid", "free": "Free"}
PUBLISHING_TYPE = {"published": "Published", "unpublished": "Unpublished"}
TOOL_TYPE = {
    "result_predictor": "Result Predictors",
    "college_predictor": "College Predictors",
    "mba_college_predictor": "MBA College Predictors",
}
TOOL_TYPE_INTEGER = {
    1: "college_predictor",
    2: "mba_college_predictor",
    3: "result_predictor",
}
FIELD_TYPE = {
    1: "Studying In",
    2: "Course Interest for College",
    3: "College Education Stream",
}
QUESTION_STATUS = {
    "Published": "Published",
    "Unpublished": "Unpublished",
    "Deleted": "Deleted",
}

STUDENT_TYPE = {1: "Overall", 2: "Category-wise"}
#Used in student appeared section
CASTE_CATEGORY = [
    {"id": caste.get("id"), "value": caste.get("name")}
    for caste in CasteCategory.objects.all().values("id", "name")
]
DISABILITY_CATEGORY = [
    {"id": disability.get("id"), "value": disability.get("name")}
    for disability in DisabilityCategory.objects.all().values("id", "name") #TODO do it using F in django
]

RP_FIELD_TYPE = {1:"User Input", 2: "Application Number", 3 : "Category Dropdown", 4 : "Select List Dropdown" , 5 : "Radio Button" , 6 : "Date of Birth"}

FORM_INPUT_PROCESS_TYPE = {1:"Score", 2:"Marks", 3:"Percentile"}

DIFFICULTY_LEVEL = {1:"Easy", 2:"Moderately Easy", 3:"Moderate", 4 :"Moderately Difficult", 5:"Difficult"}
#Used in create input form
MAPPED_CATEGORY={1:"Session", 2:"Category", 3: "Disability"}
FACTOR_TYPE = {1:"Excellent", 2:"Good", 3:"Bad", 4:"Very Bad"}
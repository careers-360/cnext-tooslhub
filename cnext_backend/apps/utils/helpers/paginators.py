"""
To paginate the query
"""
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator


def paginate_data(request, query, per_page=25, orphans=0):
	paginator = Paginator(query, per_page, orphans=orphans) # Show 25 contacts per page

	page = request.GET.get('page')
	try:
		query = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		query = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		query = paginator.page(paginator.num_pages)
	return query

# This function takes sorted list of objects and return 
# previous and next object
# used in concept and chapter mage in mainsite views
def previous_next_objects(current_object, all_objects):
	all_objects = list(all_objects)
	
	try:
		current_index = all_objects.index(current_object)
	except Exception:
		current_index = 1

	try:
		if current_index == 0:
			previous_object = None
		else:
			previous_object = all_objects[current_index - 1]
	except Exception:
		previous_object = None

	try:
		if current_index == len(all_objects) - 1:
			next_object = None
		else:
			next_object = all_objects[current_index + 1]
	except Exception:
		next_object = None

	return previous_object, next_object

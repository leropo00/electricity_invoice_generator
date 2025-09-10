
def orm_object_to_dict_exclude_default(obj, exclude_fields=None):
    exclude_default = ['id', 'created_at', 'updated_at']
    if exclude_fields:
        exclude_default.extend(exclude_fields)
    return orm_object_to_dict(obj, set(exclude_default))

def orm_object_to_dict(obj, exclude_fields=None):
    exclude_fields = exclude_fields or set()
    #Relationships aren’t part of __table__.columns, so they’re already excluded by default. 
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
        if column.name not in exclude_fields
    }
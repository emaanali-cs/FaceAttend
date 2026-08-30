from database.database import (
    get_employees,
    get_face_embeddings,
    delete_employee
)


print()
print("=" * 60)
print("CURRENT EMPLOYEES")
print("=" * 60)

employees = get_employees()

for employee in employees:

    print(
        f"ID: {employee[0]} | "
        f"Code: {employee[1]} | "
        f"Name: {employee[2]} | "
        f"Department: {employee[3]}"
    )


print()
print("=" * 60)
print("FACE EMBEDDINGS")
print("=" * 60)

embeddings = get_face_embeddings()

for record in embeddings:

    print(
        f"Employee ID: {record[0]} | "
        f"Code: {record[1]} | "
        f"Pose: {record[4]}"
    )


print()
print("=" * 60)

employee_id = input(
    "Enter the ID of the INCOMPLETE employee to delete: "
).strip()


if not employee_id.isdigit():

    print(
        "Invalid employee ID."
    )

else:

    employee_id = int(employee_id)

    delete_employee(
        employee_id
    )

    print()
    print(
        f"Employee {employee_id} deleted successfully."
    )
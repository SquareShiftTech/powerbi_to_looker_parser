# Model: education_24b04535


explore: fact_enrollments {
  
  label: "fact_enrollments"
  
  
  join: dim_courses {
    type: left_outer
    relationship: many_to_one
    sql_on: ${fact_enrollments.course_id} = ${dim_courses.course_id} ;;
    
    # Relationship type defaulted to many_to_one - verify cardinality
    
  }
  
  join: dim_date {
    type: left_outer
    relationship: many_to_one
    sql_on: ${fact_enrollments.enrollment_date} = ${dim_date.full_date} ;;
    
    # Relationship type defaulted to many_to_one - verify cardinality
    
  }
  
}


explore: dim_faculty {
  
  label: "dim_faculty"
  
  
  join: localdatetable_a5fd9646_2978_429d_bb4f_ce757eecfbb5 {
    type: left_outer
    relationship: many_to_one
    sql_on: ${dim_faculty.joining_date} = ${localdatetable_a5fd9646_2978_429d_bb4f_ce757eecfbb5.Date} ;;
    
    # Relationship type defaulted to many_to_one - verify cardinality
    
  }
  
}


explore: dim_departments {
  
  label: "dim_departments"
  
  
}


explore: dim_courses {
  
  label: "dim_courses"
  
  
  join: dim_faculty {
    type: left_outer
    relationship: many_to_one
    sql_on: ${dim_courses.faculty_id} = ${dim_faculty.faculty_id} ;;
    
    # Relationship type defaulted to many_to_one - verify cardinality
    
  }
  
  join: dim_departments {
    type: left_outer
    relationship: many_to_one
    sql_on: ${dim_courses.department_id} = ${dim_departments.department_id} ;;
    
    # Relationship type defaulted to many_to_one - verify cardinality
    
  }
  
}


explore: dim_date {
  
  label: "dim_date"
  
  
  join: localdatetable_9f303140_d25a_49b9_9054_89a40283ed3c {
    type: left_outer
    relationship: many_to_one
    sql_on: ${dim_date.full_date} = ${localdatetable_9f303140_d25a_49b9_9054_89a40283ed3c.Date} ;;
    
    # Relationship type defaulted to many_to_one - verify cardinality
    
  }
  
}


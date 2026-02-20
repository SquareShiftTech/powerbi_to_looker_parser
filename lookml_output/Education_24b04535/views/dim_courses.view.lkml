
view: dim_courses {

  
  sql_table_name: `tableau-to-looker-migration.education.dim_courses` ;;
  

  
  
  
  # Original DAX: AVERAGE(dim_courses[credits])
  
  # Converted: auto
  
  
  dimension: avg_credits {
    type: number
    sql: NULL ;;
    
    label: "Avg Credits"
    
  }
  
  
  
  
  dimension: course_code {
    type: string
    sql: ${TABLE}.course_code ;;
    
    label: "course_code"
    
  }
  
  
  
  
  dimension: course_id {
    type: string
    sql: ${TABLE}.course_id ;;
    
    label: "course_id"
    
  }
  
  
  
  
  dimension: course_name {
    type: string
    sql: ${TABLE}.course_name ;;
    
    label: "course_name"
    
  }
  
  
  
  
  dimension: course_type {
    type: string
    sql: ${TABLE}.course_type ;;
    
    label: "course_type"
    
  }
  
  
  
  
  # Original DAX: DIVIDE([Total Enrollments], [Total Course Capacity], 0) *100
  
  # Converted: auto
  
  
  dimension: course_utilization {
    type: number
    sql: NULL ;;
    
    label: "Course Utilization"
    
  }
  
  
  
  
  dimension: department_id {
    type: string
    sql: ${TABLE}.department_id ;;
    
    label: "department_id"
    
  }
  
  
  
  
  dimension: faculty_id {
    type: string
    sql: ${TABLE}.faculty_id ;;
    
    label: "faculty_id"
    
  }
  
  
  
  
  dimension: prerequisite_course_id {
    type: string
    sql: ${TABLE}.prerequisite_course_id ;;
    
    label: "prerequisite_course_id"
    
  }
  
  
  
  
  dimension: semester_offered {
    type: number
    sql: ${TABLE}.semester_offered ;;
    
    label: "semester_offered"
    
  }
  
  
  
  
  # Original DAX: SUM(dim_courses[max_students])
  
  # Converted: auto
  
  
  dimension: total_course_capacity {
    type: number
    sql: NULL ;;
    
    label: "Total Course Capacity"
    
  }
  
  
  
  
  # Original DAX: COUNT(dim_courses[course_id])
  
  # Converted: auto
  
  
  dimension: total_courses {
    type: number
    sql: NULL ;;
    
    label: "Total Courses"
    
  }
  
  
  
  
  
  dimension: credits_measure {
    type: sum
    sql: ${TABLE}.credits ;;
    
  }

  measure: credits {
    type: sum
    sql: ${ credits_measure } ;;
    
    
    label: "credits"
    
  }
  
  
  
  
  
  dimension: max_students_measure {
    type: sum
    sql: ${TABLE}.max_students ;;
    
  }

  measure: max_students {
    type: sum
    sql: ${ max_students_measure } ;;
    
    
    label: "max_students"
    
  }
  
  
}
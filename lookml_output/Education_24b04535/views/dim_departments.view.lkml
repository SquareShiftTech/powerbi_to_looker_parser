
view: dim_departments {

  
  sql_table_name: `tableau-to-looker-migration.education.dim_departments` ;;
  

  
  
  
  # Original DAX: AVERAGE(dim_departments[budget_allocated])
  
  # Converted: auto
  
  
  dimension: avg_department_budget {
    type: number
    sql: NULL ;;
    
    label: "Avg Department Budget"
    
  }
  
  
  
  
  dimension: budget_allocated {
    type: number
    sql: ${TABLE}.budget_allocated ;;
    
    label: "budget_allocated"
    
  }
  
  
  
  
  dimension: building {
    type: string
    sql: ${TABLE}.building ;;
    
    label: "building"
    
  }
  
  
  
  
  dimension: contact_email {
    type: string
    sql: ${TABLE}.contact_email ;;
    
    label: "contact_email"
    
  }
  
  
  
  
  dimension: department_code {
    type: string
    sql: ${TABLE}.department_code ;;
    
    label: "department_code"
    
  }
  
  
  
  
  dimension: department_id {
    type: string
    sql: ${TABLE}.department_id ;;
    
    label: "department_id"
    
  }
  
  
  
  
  dimension: department_name {
    type: string
    sql: ${TABLE}.department_name ;;
    
    label: "department_name"
    
  }
  
  
  
  
  dimension: established_year {
    type: number
    sql: ${TABLE}.established_year ;;
    
    label: "established_year"
    
  }
  
  
  
  
  # Original DAX: DIVIDE(SUM(dim_departments[total_faculty]), SUM(dim_departments[total_students]), 0)
  
  # Converted: auto
  
  
  dimension: faculty_student_ratio {
    type: number
    sql: NULL ;;
    
    label: "Faculty Student Ratio"
    
  }
  
  
  
  
  dimension: floor {
    type: string
    sql: ${TABLE}.floor ;;
    
    label: "floor"
    
  }
  
  
  
  
  dimension: head_of_department {
    type: string
    sql: ${TABLE}.head_of_department ;;
    
    label: "head_of_department"
    
  }
  
  
  
  
  # Original DAX: SUM(dim_departments[budget_allocated])
  
  # Converted: auto
  
  
  dimension: total_budget {
    type: number
    sql: NULL ;;
    
    label: "Total Budget"
    
  }
  
  
  
  
  # Original DAX: COUNT(dim_departments[department_id])
  
  # Converted: auto
  
  
  dimension: total_departments {
    type: number
    sql: NULL ;;
    
    label: "Total Departments"
    
  }
  
  
  
  
  dimension: total_faculty {
    type: number
    sql: ${TABLE}.total_faculty ;;
    
    label: "total_faculty"
    
  }
  
  
  
  
  dimension: total_students {
    type: number
    sql: ${TABLE}.total_students ;;
    
    label: "total_students"
    
  }
  
  
}
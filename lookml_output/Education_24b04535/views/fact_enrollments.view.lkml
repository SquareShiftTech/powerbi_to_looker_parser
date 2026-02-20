
view: fact_enrollments {

  
  sql_table_name: `tableau-to-looker-migration.education.fact_enrollments` ;;
  

  
  
  
  dimension: academic_year {
    type: string
    sql: ${TABLE}.academic_year ;;
    
    label: "academic_year"
    
  }
  
  
  
  
  # Original DAX: AVERAGE(fact_enrollments[attendance_percentage])
  
  # Converted: auto
  
  
  dimension: avg_attendance {
    type: number
    sql: NULL ;;
    
    label: "Avg Attendance"
    
  }
  
  
  
  
  # Original DAX: AVERAGE(fact_enrollments[total_marks])
  
  # Converted: auto
  
  
  dimension: avg_total_marks {
    type: number
    sql: NULL ;;
    
    label: "Avg Total Marks"
    
  }
  
  
  
  
  dimension: course_id {
    type: string
    sql: ${TABLE}.course_id ;;
    
    label: "course_id"
    
  }
  
  
  
  
  dimension: enrollment_id {
    type: string
    sql: ${TABLE}.enrollment_id ;;
    
    label: "enrollment_id"
    
  }
  
  
  
  
  dimension: grade {
    type: string
    sql: ${TABLE}.grade ;;
    
    label: "grade"
    
  }
  
  
  
  
  # Original DAX: DIVIDE(
    CALCULATE(COUNT(fact_enrollments[enrollment_id]), fact_enrollments[status] = "Passed"),
    COUNT(fact_enrollments[enrollment_id])
)
  
  # Converted: auto
  
  
  dimension: pass_rate {
    type: number
    sql: NULL ;;
    
    label: "Pass Rate"
    
  }
  
  
  
  
  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
    
    label: "status"
    
  }
  
  
  
  
  dimension: student_id {
    type: string
    sql: ${TABLE}.student_id ;;
    
    label: "student_id"
    
  }
  
  
  
  
  # Original DAX: SUM(fact_enrollments[total_marks])
  
  # Converted: auto
  
  
  dimension: sum_marks {
    type: number
    sql: NULL ;;
    
    label: "sum marks"
    
  }
  
  
  
  
  # Original DAX: COUNT(fact_enrollments[enrollment_id])
  
  # Converted: auto
  
  
  dimension: total_enrollments {
    type: number
    sql: NULL ;;
    
    label: "Total Enrollments"
    
  }
  
  
  
  
  dimension: total_marks {
    type: number
    sql: ${TABLE}.total_marks ;;
    
    label: "total_marks"
    
  }
  
  
  
  dimension_group: enrollment_date {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.enrollment_date ;;
    
    label: "enrollment_date"
    
  }
  
  
  
  
  
  dimension: attendance_percentage_measure {
    type: sum
    sql: ${TABLE}.attendance_percentage ;;
    
  }

  measure: attendance_percentage {
    type: sum
    sql: ${ attendance_percentage_measure } ;;
    
    
    label: "attendance_percentage"
    
  }
  
  
  
  
  
  dimension: credits_earned_measure {
    type: sum
    sql: ${TABLE}.credits_earned ;;
    
  }

  measure: credits_earned {
    type: sum
    sql: ${ credits_earned_measure } ;;
    
    
    label: "credits_earned"
    
  }
  
  
  
  
  
  dimension: external_marks_measure {
    type: sum
    sql: ${TABLE}.external_marks ;;
    
  }

  measure: external_marks {
    type: sum
    sql: ${ external_marks_measure } ;;
    
    
    label: "external_marks"
    
  }
  
  
  
  
  
  dimension: internal_marks_measure {
    type: sum
    sql: ${TABLE}.internal_marks ;;
    
  }

  measure: internal_marks {
    type: sum
    sql: ${ internal_marks_measure } ;;
    
    
    label: "internal_marks"
    
  }
  
  
  
  
  
  dimension: semester_measure {
    type: sum
    sql: ${TABLE}.semester ;;
    
  }

  measure: semester {
    type: sum
    sql: ${ semester_measure } ;;
    
    
    label: "semester"
    
  }
  
  
}

view: dim_faculty {

  
  sql_table_name: `tableau-to-looker-migration.education.dim_faculty` ;;
  

  
  
  
  # Original DAX: AVERAGE(dim_faculty[years_of_experience])
  
  # Converted: auto
  
  
  dimension: avg_experience {
    type: number
    sql: NULL ;;
    
    label: "Avg Experience"
    
  }
  
  
  
  
  # Original DAX: AVERAGE(dim_faculty[salary])
  
  # Converted: auto
  
  
  dimension: avg_salary {
    type: number
    sql: NULL ;;
    
    label: "Avg Salary"
    
  }
  
  
  
  
  dimension: department_id {
    type: string
    sql: ${TABLE}.department_id ;;
    
    label: "department_id"
    
  }
  
  
  
  
  dimension: designation {
    type: string
    sql: ${TABLE}.designation ;;
    
    label: "designation"
    
  }
  
  
  
  
  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
    
    label: "email"
    
  }
  
  
  
  
  # Original DAX: CALCULATE(
    [sum salary],
    DATEADD(dim_faculty[joining_date].[Date], -1, MONTH)
)
  
  # Converted: auto
  
  
  dimension: faculty_hired_last_month {
    type: number
    sql: NULL ;;
    
    label: "Faculty Hired Last Month"
    
  }
  
  
  
  
  # Original DAX: CALCULATE(
    [sum salary],
    SAMEPERIODLASTYEAR(dim_faculty[joining_date].[Date])
)
  
  # Converted: auto
  
  
  dimension: faculty_hired_last_year {
    type: number
    sql: NULL ;;
    
    label: "Faculty Hired Last Year"
    
  }
  
  
  
  
  # Original DAX: CALCULATE(
    [sum salary],
    DATESMTD(dim_faculty[joining_date].[Date])
)
  
  # Converted: auto
  
  
  dimension: faculty_hired_mtd {
    type: number
    sql: NULL ;;
    
    label: "Faculty Hired MTD"
    
  }
  
  
  
  
  # Original DAX: CALCULATE(
    [sum salary],
    DATESQTD(dim_faculty[joining_date].[Date])
)
  
  # Converted: auto
  
  
  dimension: faculty_hired_qtd {
    type: number
    sql: NULL ;;
    
    label: "Faculty Hired QTD"
    
  }
  
  
  
  
  # Original DAX: CALCULATE(
    [sum salary],
    DATESYTD(dim_faculty[joining_date].[Date])
)
  
  # Converted: auto
  
  
  dimension: faculty_hired_ytd {
    type: number
    sql: NULL ;;
    
    label: "Faculty Hired YTD"
    
  }
  
  
  
  
  dimension: faculty_id {
    type: string
    sql: ${TABLE}.faculty_id ;;
    
    label: "faculty_id"
    
  }
  
  
  
  
  dimension: first_name {
    type: string
    sql: ${TABLE}.first_name ;;
    
    label: "first_name"
    
  }
  
  
  
  
  dimension: last_name {
    type: string
    sql: ${TABLE}.last_name ;;
    
    label: "last_name"
    
  }
  
  
  
  
  dimension: qualification {
    type: string
    sql: ${TABLE}.qualification ;;
    
    label: "qualification"
    
  }
  
  
  
  
  dimension: salary {
    type: number
    sql: ${TABLE}.salary ;;
    
    label: "salary"
    
  }
  
  
  
  
  # Original DAX: RANK(ORDERBY([salary], DESC))
  
  # Converted: auto
  
  
  dimension: salary_rank {
    type: number
    sql: NULL ;;
    
    label: "Salary Rank"
    
  }
  
  
  
  
  dimension: specialization {
    type: string
    sql: ${TABLE}.specialization ;;
    
    label: "specialization"
    
  }
  
  
  
  
  # Original DAX: SUM(dim_faculty[salary])
  
  # Converted: auto
  
  
  dimension: sum_salary {
    type: number
    sql: NULL ;;
    
    label: "sum salary"
    
  }
  
  
  
  
  # Original DAX: COUNT(dim_faculty[faculty_id])
  
  # Converted: auto
  
  
  dimension: total_faculty {
    type: number
    sql: NULL ;;
    
    label: "Total Faculty"
    
  }
  
  
  
  
  # Original DAX: SUM(dim_faculty[publications])
  
  # Converted: auto
  
  
  dimension: total_publications {
    type: number
    sql: NULL ;;
    
    label: "Total Publications"
    
  }
  
  
  
  dimension_group: joining_date {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.joining_date ;;
    
    label: "joining_date"
    
  }
  
  
  
  
  
  dimension: phone_measure {
    type: sum
    sql: ${TABLE}.phone ;;
    
  }

  measure: phone {
    type: sum
    sql: ${ phone_measure } ;;
    
    
    label: "phone"
    
  }
  
  
  
  
  
  dimension: publications_measure {
    type: sum
    sql: ${TABLE}.publications ;;
    
  }

  measure: publications {
    type: sum
    sql: ${ publications_measure } ;;
    
    
    label: "publications"
    
  }
  
  
  
  
  
  dimension: research_projects_measure {
    type: sum
    sql: ${TABLE}.research_projects ;;
    
  }

  measure: research_projects {
    type: sum
    sql: ${ research_projects_measure } ;;
    
    
    label: "research_projects"
    
  }
  
  
  
  
  
  dimension: years_of_experience_measure {
    type: sum
    sql: ${TABLE}.years_of_experience ;;
    
  }

  measure: years_of_experience {
    type: sum
    sql: ${ years_of_experience_measure } ;;
    
    
    label: "years_of_experience"
    
  }
  
  
}
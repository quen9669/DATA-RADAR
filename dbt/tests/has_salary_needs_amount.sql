select * from {{ ref('offers') }} where has_salary and (salary_eur_year is null or salary_origin <> 'employeur')

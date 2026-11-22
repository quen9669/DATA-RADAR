select * from {{ ref('salaries') }} where salary_eur_min is null or salary_eur_max is null or salary_eur_min > salary_eur_max

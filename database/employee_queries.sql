-- Employee Attrition Analytics: Example SQL Queries
-- These queries demonstrate inserting and retrieving data
-- from the relational employee database.

-- INSERT A SAMPLE EMPLOYEE RECORD
INSERT INTO Employee (
    EmployeeID,
    DepartmentID,
    JobRoleID,
    JobLevelID,
    MaritalStatusID,
    BusinessTravelID,
    Gender,
    Age,
    DistanceFromHome,
    YearsAtCompany,
    CompanyTenure,
    MonthlyIncome,
    NumDependents,
    YearsSinceLastPromotion,
    PromotionCount,
    RemoteWorkFlag,
    JobSatisfaction,
    WorkLifeBalance,
    EnvironmentSatisfaction,
    PerformanceRating,
    AttritionFlag
)
VALUES (
    91000,
    1,
    3,
    2,
    2,
    1,
    'F',
    29,
    10,
    5,
    5,
    4200.00,
    0,
    1,
    0,
    'Y',
    2,
    3,
    3,
    3,
    0
);

-- EMPLOYEES WITH NO PROMOTIONS AND 5+ YEARS AT THE COMPANY
SELECT *
FROM Employee
WHERE PromotionCount = 0
  AND YearsAtCompany >= 5;

-- AVERAGE MONTHLY INCOME FOR LOW JOB SATISFACTION
SELECT AVG(MonthlyIncome) AS AvgMonthlyIncome
FROM Employee
WHERE JobSatisfaction <= 2
  AND MonthlyIncome IS NOT NULL;

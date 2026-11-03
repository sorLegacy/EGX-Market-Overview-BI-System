USE Sigma_Cap;
GO

DROP TABLE IF EXISTS Dim_Date;
GO

CREATE TABLE Dim_Date (
    DateKey DATE PRIMARY KEY,
    [Year] INT,
    [Quarter] VARCHAR(5),
    [Month] INT,
    [MonthName] VARCHAR(20),
    [Day] INT,
    [DayOfWeekName] VARCHAR(20),
    [IsTradingDay] BIT
);
GO

-- Populate 2026 Calendar
WITH DateSequence AS (
    SELECT CAST('2026-10-01' AS DATE) AS CalendarDate
    UNION ALL
    SELECT DATEADD(day, 1, CalendarDate)
    FROM DateSequence
    WHERE CalendarDate < '2026-12-31'
)
INSERT INTO Dim_Date (DateKey, [Year], [Quarter], [Month], [MonthName], [Day], [DayOfWeekName], [IsTradingDay])
SELECT 
    CalendarDate,
    YEAR(CalendarDate),
    'Q' + CAST(DATEPART(quarter, CalendarDate) AS VARCHAR),
    MONTH(CalendarDate),
    DATENAME(month, CalendarDate),
    DAY(CalendarDate),
    DATENAME(weekday, CalendarDate),
    CASE WHEN DATENAME(weekday, CalendarDate) IN ('Friday', 'Saturday') THEN 0 ELSE 1 END
FROM DateSequence
OPTION (MAXRECURSION 366);
GO
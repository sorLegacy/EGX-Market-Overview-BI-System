--------------------------------------------------------------------------------
-- Sigma_Cap Database & Complete Star Schema DDL Script
-- Project 2: Sigma Capital Market Overview & Trading Reports
-- All direct and computed requirements mapped and created.
--------------------------------------------------------------------------------

USE master;
GO

-- 1. Create Database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'Sigma_Cap')
BEGIN
    CREATE DATABASE Sigma_Cap;
    PRINT 'Database Sigma_Cap created successfully.';
END
ELSE
BEGIN
    PRINT 'Database Sigma_Cap already exists.';
END
GO

USE Sigma_Cap;
GO

--------------------------------------------------------------------------------
-- 2. Fact Tables with all Computed Metrics
--------------------------------------------------------------------------------

-- A. Market Breadth Fact Table (Scope 3)
-- Metrics: Advancing, Declining, Unchanged, Total, Advance/Decline Ratio
IF OBJECT_ID('dbo.fact_market_breadth', 'U') IS NOT NULL DROP TABLE dbo.fact_market_breadth;
CREATE TABLE dbo.fact_market_breadth (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    trading_date    DATE NOT NULL,
    advancing_count INT NOT NULL,
    declining_count INT NOT NULL,
    unchanged_count INT NOT NULL,
    total_stocks    INT NOT NULL,
    ad_ratio        DECIMAL(10, 4) NULL, -- Computed: Advancing / Declining
    created_at      DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_breadth_date UNIQUE (trading_date)
);
PRINT 'Table fact_market_breadth created.';
GO


-- B. Sector Activity Fact Table (Scope 4)
-- Metrics: Sector Name, Turnover Mn, Market Share %, Computed Market Share %
IF OBJECT_ID('dbo.fact_sector_activity', 'U') IS NOT NULL DROP TABLE dbo.fact_sector_activity;
CREATE TABLE dbo.fact_sector_activity (
    id                         INT IDENTITY(1,1) PRIMARY KEY,
    trading_date               DATE NOT NULL,
    sector_name                NVARCHAR(150) NOT NULL,
    turnover_mn                DECIMAL(18, 2) NOT NULL,
    direct_market_share_pct    DECIMAL(5, 2) NOT NULL,
    computed_market_share_pct  DECIMAL(5, 2) NULL, -- Computed: Sector T/O / Total Daily Sector T/O * 100
    created_at                 DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_sector_date UNIQUE (trading_date, sector_name)
);
PRINT 'Table fact_sector_activity created.';
GO


-- C. Normalized Investors Distribution Fact Table (Scopes 1 & 2)
-- Metrics: Buy Value, Sell Value, Net Value, Turnover, Trading %
IF OBJECT_ID('dbo.fact_investors_distribution', 'U') IS NOT NULL DROP TABLE dbo.fact_investors_distribution;
CREATE TABLE dbo.fact_investors_distribution (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    trading_date   DATE NOT NULL,
    nationality    NVARCHAR(50) NOT NULL,    -- 'Egyptian', 'Arab', 'Foreign'
    category       NVARCHAR(50) NOT NULL,       -- 'Retail', 'Institutional'
    buy_value_mn   DECIMAL(18, 2) NOT NULL,
    sell_value_mn  DECIMAL(18, 2) NOT NULL,
    net_value_mn   DECIMAL(18, 2) NOT NULL,     -- Computed: [Buy Value] - [Sell Value]
    turnover_mn    DECIMAL(18, 2) NOT NULL,
    trading_pct    DECIMAL(5, 2) NOT NULL,
    created_at     DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_investors_date_cat UNIQUE (trading_date, nationality, category)
);
PRINT 'Table fact_investors_distribution created.';
GO


-- D. Daily Investor Aggregate Breakdown Fact Table (Scope 1 Summary)
-- Metrics: Egyptian %, Arab %, Foreign %, Local Institutions %, Retail vs Inst %
IF OBJECT_ID('dbo.fact_daily_investor_summary', 'U') IS NOT NULL DROP TABLE dbo.fact_daily_investor_summary;
CREATE TABLE dbo.fact_daily_investor_summary (
    id                    INT IDENTITY(1,1) PRIMARY KEY,
    trading_date          DATE NOT NULL,
    egyptian_pct          DECIMAL(5, 2) NOT NULL, -- Egyptian Ret. % + Egyptian Inst. %
    arab_pct              DECIMAL(5, 2) NOT NULL, -- Arab Ret. % + Arab Inst. %
    foreign_pct           DECIMAL(5, 2) NOT NULL, -- Foreign Ret. % + Foreign Inst. %
    local_institutions_pct DECIMAL(5, 2) NOT NULL, -- Egyptian Inst. %
    retail_pct            DECIMAL(5, 2) NOT NULL, -- Total Ret. %
    institutional_pct     DECIMAL(5, 2) NOT NULL, -- Total Inst. %
    created_at            DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_investor_summary_date UNIQUE (trading_date)
);
PRINT 'Table fact_daily_investor_summary created.';
GO


-- E. Block Trades Fact Table (Scope 5)
-- Metrics: Ticker, Quantity, Value EGP, Deals, Avg Price, Block % of Market
IF OBJECT_ID('dbo.fact_block_trades', 'U') IS NOT NULL DROP TABLE dbo.fact_block_trades;
CREATE TABLE dbo.fact_block_trades (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    trading_date        DATE NOT NULL,
    share_name          NVARCHAR(200) NOT NULL,
    quantity            BIGINT NOT NULL,
    value_egp           DECIMAL(18, 2) NOT NULL,
    trade_count         INT NOT NULL,
    avg_price           DECIMAL(18, 4) NOT NULL, -- Computed: Value EGP / Quantity
    block_pct_of_market DECIMAL(8, 4) NULL,      -- Computed: Block Value / Total Market Turnover * 100
    created_at          DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_block_trade UNIQUE (trading_date, share_name, quantity, value_egp)
);
PRINT 'Table fact_block_trades created.';
GO


-- F. Market Indices Fact Table
IF OBJECT_ID('dbo.fact_market_indices', 'U') IS NOT NULL DROP TABLE dbo.fact_market_indices;
CREATE TABLE dbo.fact_market_indices (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    trading_date DATE NOT NULL,
    index_name   NVARCHAR(50) NOT NULL, -- 'EGX30', 'EGX100', 'EGX70E', 'EGX30C'
    last_value   DECIMAL(18, 2) NOT NULL,
    change_pts   DECIMAL(18, 2) NULL,
    change_pct   DECIMAL(5, 2) NULL,
    created_at   DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_indices_date UNIQUE (trading_date, index_name)
);
PRINT 'Table fact_market_indices created.';
GO


-- G. Stock Leaderboards Fact Table (Turnover, Volume, Gainers, Losers, Fluctuation)
IF OBJECT_ID('dbo.fact_stock_leaderboards', 'U') IS NOT NULL DROP TABLE dbo.fact_stock_leaderboards;
CREATE TABLE dbo.fact_stock_leaderboards (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    trading_date DATE NOT NULL,
    board_type   NVARCHAR(50) NOT NULL, -- 'Turnover', 'Volume', 'Best Performers', 'Worst Performers', 'Largest Fluctuation'
    ticker       NVARCHAR(50) NOT NULL,
    last_price   DECIMAL(18, 4) NULL,
    change_pts   DECIMAL(18, 2) NULL,
    change_pct   DECIMAL(5, 2) NULL,
    turnover_mn  DECIMAL(18, 2) NULL,
    volume_mn    DECIMAL(18, 4) NULL,
    high_price   DECIMAL(18, 4) NULL,
    low_price    DECIMAL(18, 4) NULL,
    created_at   DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_fact_leaderboard_date UNIQUE (trading_date, board_type, ticker)
);
PRINT 'Table fact_stock_leaderboards created.';
GO


--------------------------------------------------------------------------------
-- 3. Analytical Views for Direct Power BI Reporting
--------------------------------------------------------------------------------

-- Summary View: Investor Daily Flow by Nationality
IF OBJECT_ID('dbo.vw_Investor_Nationality_Summary', 'V') IS NOT NULL DROP VIEW dbo.vw_Investor_Nationality_Summary;
GO
CREATE VIEW dbo.vw_Investor_Nationality_Summary AS
SELECT 
    trading_date,
    nationality,
    SUM(buy_value_mn)  AS total_buy_mn,
    SUM(sell_value_mn) AS total_sell_mn,
    SUM(net_value_mn)  AS net_flow_mn,
    SUM(turnover_mn)   AS total_turnover_mn,
    SUM(trading_pct)   AS total_trading_pct
FROM dbo.fact_investors_distribution
GROUP BY trading_date, nationality;
GO
PRINT 'View vw_Investor_Nationality_Summary created.';

-- Summary View: Retail vs Institutional Daily Split
IF OBJECT_ID('dbo.vw_Retail_vs_Institutional', 'V') IS NOT NULL DROP VIEW dbo.vw_Retail_vs_Institutional;
GO
CREATE VIEW dbo.vw_Retail_vs_Institutional AS
SELECT 
    trading_date,
    category,
    SUM(buy_value_mn)  AS total_buy_mn,
    SUM(sell_value_mn) AS total_sell_mn,
    SUM(net_value_mn)  AS net_flow_mn,
    SUM(turnover_mn)   AS total_turnover_mn,
    SUM(trading_pct)   AS total_trading_pct
FROM dbo.fact_investors_distribution
GROUP BY trading_date, category;
GO
PRINT 'View vw_Retail_vs_Institutional created.';
GO

--------------------------------------------------------------------------------
-- 4. Verification Query
--------------------------------------------------------------------------------
SELECT 
    TABLE_SCHEMA,
    TABLE_NAME,
    TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_TYPE, TABLE_NAME;
GO

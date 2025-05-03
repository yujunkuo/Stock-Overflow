# User Strategy API Documentation

This API allows users to create, retrieve, update, and delete custom trading strategies. A strategy is a collection of rules that can be applied to stock data to filter stocks based on various criteria.

## API Endpoints

### Get Available Rule Types

```
GET /strategy/rule-types
```

Returns a list of all available rule types that can be used to create a strategy.

**Response**

```json
[
  "PERangeRule",
  "PBRangeRule",
  "DividendYieldRangeRule",
  "SMARule",
  "CrossAboveRule",
  "CrossBelowRule",
  "RSIRule",
  "MACDRule",
  "BollingerBandsRule",
  "VolumeRule",
  "ForeignInvestorsRule",
  "InvestmentTrustRule",
  "DealersRule",
  "MarginTradingRule",
  "ShortSellingRule"
]
```

### Create a Strategy

```
POST /strategy/user/{user_id}/strategies
```

Creates a new strategy for the specified user.

**Request Body**

```json
{
  "name": "My Strategy",
  "description": "A strategy that combines PE and RSI",
  "rules": [
    {
      "type": "PERangeRule",
      "column": "pe_ratio",
      "comparison_type": "LESS_THAN",
      "threshold_1": 15,
      "name": "Low PE",
      "description": "PE ratio less than 15"
    },
    {
      "type": "RSIRule",
      "days": 14,
      "comparison_type": "LESS_THAN",
      "threshold_1": 30,
      "name": "Oversold RSI",
      "description": "RSI less than 30"
    }
  ]
}
```

**Response (201 Created)**

```json
{
  "user_id": "user123",
  "name": "My Strategy",
  "description": "A strategy that combines PE and RSI",
  "rules": [
    {
      "type": "PERangeRule",
      "name": "Low PE",
      "description": "PE ratio less than 15",
      "column": "pe_ratio",
      "comparison_type": "LESS_THAN",
      "threshold_1": 15
    },
    {
      "type": "RSIRule",
      "name": "Oversold RSI",
      "description": "RSI less than 30",
      "days": 14,
      "comparison_type": "LESS_THAN",
      "threshold_1": 30
    }
  ],
  "metadata": {
    "created_at": "2023-05-20T12:34:56.789Z",
    "updated_at": "2023-05-20T12:34:56.789Z"
  }
}
```

### Get All Strategies for a User

```
GET /strategy/user/{user_id}/strategies
```

Returns all strategies for the specified user.

**Response**

```json
[
  {
    "user_id": "user123",
    "name": "My Strategy",
    "description": "A strategy that combines PE and RSI",
    "rules": [
      {
        "type": "PERangeRule",
        "name": "Low PE",
        "description": "PE ratio less than 15",
        "column": "pe_ratio",
        "comparison_type": "LESS_THAN",
        "threshold_1": 15
      },
      {
        "type": "RSIRule",
        "name": "Oversold RSI",
        "description": "RSI less than 30",
        "days": 14,
        "comparison_type": "LESS_THAN",
        "threshold_1": 30
      }
    ],
    "metadata": {
      "created_at": "2023-05-20T12:34:56.789Z",
      "updated_at": "2023-05-20T12:34:56.789Z"
    }
  }
]
```

### Get a Specific Strategy

```
GET /strategy/user/{user_id}/strategies/{strategy_name}
```

Returns a specific strategy.

**Response**

```json
{
  "user_id": "user123",
  "name": "My Strategy",
  "description": "A strategy that combines PE and RSI",
  "rules": [
    {
      "type": "PERangeRule",
      "name": "Low PE",
      "description": "PE ratio less than 15",
      "column": "pe_ratio",
      "comparison_type": "LESS_THAN",
      "threshold_1": 15
    },
    {
      "type": "RSIRule",
      "name": "Oversold RSI",
      "description": "RSI less than 30",
      "days": 14,
      "comparison_type": "LESS_THAN",
      "threshold_1": 30
    }
  ],
  "metadata": {
    "created_at": "2023-05-20T12:34:56.789Z",
    "updated_at": "2023-05-20T12:34:56.789Z"
  }
}
```

### Update a Strategy

```
PUT /strategy/user/{user_id}/strategies/{strategy_name}
```

Updates a specific strategy.

**Request Body**

```json
{
  "description": "Updated description",
  "rules": [
    {
      "type": "PERangeRule",
      "column": "pe_ratio",
      "comparison_type": "LESS_THAN",
      "threshold_1": 10,
      "name": "Very Low PE",
      "description": "PE ratio less than 10"
    }
  ]
}
```

**Response**

```json
{
  "user_id": "user123",
  "name": "My Strategy",
  "description": "Updated description",
  "rules": [
    {
      "type": "PERangeRule",
      "name": "Very Low PE",
      "description": "PE ratio less than 10",
      "column": "pe_ratio",
      "comparison_type": "LESS_THAN",
      "threshold_1": 10
    }
  ],
  "metadata": {
    "created_at": "2023-05-20T12:34:56.789Z",
    "updated_at": "2023-05-20T13:45:56.789Z"
  }
}
```

### Delete a Strategy

```
DELETE /strategy/user/{user_id}/strategies/{strategy_name}
```

Deletes a specific strategy.

**Response (204 No Content)**

### Execute a Strategy

```
POST /strategy/execute
```

Executes a strategy on stock data.

**Request Body**

```json
{
  "strategy": {
    "user_id": "user123",
    "name": "My Strategy",
    "description": "A strategy that combines PE and RSI",
    "rules": [
      {
        "type": "PERangeRule",
        "name": "Low PE",
        "description": "PE ratio less than 15",
        "column": "pe_ratio",
        "comparison_type": "LESS_THAN",
        "threshold_1": 15
      },
      {
        "type": "RSIRule",
        "name": "Oversold RSI",
        "description": "RSI less than 30",
        "days": 14,
        "comparison_type": "LESS_THAN",
        "threshold_1": 30
      }
    ]
  },
  "stock_data": [
    {
      "symbol": "AAPL",
      "pe_ratio": 12.5,
      "rsi_14": 28.5
    },
    {
      "symbol": "MSFT",
      "pe_ratio": 20.1,
      "rsi_14": 45.2
    },
    {
      "symbol": "GOOG",
      "pe_ratio": 14.2,
      "rsi_14": 29.1
    }
  ]
}
```

**Response**

```json
[
  {
    "symbol": "AAPL",
    "pe_ratio": 12.5,
    "rsi_14": 28.5
  },
  {
    "symbol": "GOOG",
    "pe_ratio": 14.2,
    "rsi_14": 29.1
  }
]
```

## Rule Types and Parameters

Different rule types require different parameters. Here are the parameters for each rule type:

### Fundamental Rules

#### PERangeRule

- `column`: The column containing the PE ratio
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### PBRangeRule

- `column`: The column containing the PB ratio
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### DividendYieldRangeRule

- `column`: The column containing the dividend yield
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

### Technical Rules

#### SMARule

- `days`: Number of days for the SMA
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### CrossAboveRule

- `indicator_1`: First indicator (e.g., "close")
- `indicator_2`: Second indicator (e.g., "sma_20")
- `days`: Number of days to look back

#### CrossBelowRule

- `indicator_1`: First indicator (e.g., "close")
- `indicator_2`: Second indicator (e.g., "sma_20")
- `days`: Number of days to look back

#### RSIRule

- `days`: Number of days for the RSI
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### MACDRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### BollingerBandsRule

- `days`: Number of days for the Bollinger Bands
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### VolumeRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

### Chip Rules

#### ForeignInvestorsRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### InvestmentTrustRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### DealersRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### MarginTradingRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison)

#### ShortSellingRule

- `days`: Number of days to look back
- `comparison_type`: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
- `threshold_1`: First threshold value
- `threshold_2`: Second threshold value (required for BETWEEN comparison) 
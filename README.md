# TOPSIS Decision Support System

A comprehensive web-based Decision Support System that implements the TOPSIS (Technique for Order Preference by Similarity to an Ideal Solution) method for multi-criteria decision making.

## Features

- **User Authentication**: Register, login, and secure session management
- **Project Management**: Create, edit, and manage multiple decision projects
- **Criteria Management**: Add, edit criteria with benefit/cost types and weights
- **Alternative Management**: Add alternatives with criterion values
- **TOPSIS Calculation**: Automatic calculation with detailed step-by-step results
- **CSV Import/Export**: Import data from CSV files and export results
- **Dark/Light Mode**: Toggle between themes for better user experience
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy
- **Frontend**: React with TypeScript and Material-UI
- **Database**: SQLite (default) or PostgreSQL/MySQL
- **Authentication**: JWT tokens
- **Data Processing**: Pandas, NumPy

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DecisionSupportSystem
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the Flask backend
python app.py
```

The backend will start on `http://localhost:5000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the React development server
npm start
```

The frontend will start on `http://localhost:3000`

## Usage

### 1. Registration & Login

1. Open `http://localhost:3000` in your browser
2. Click "Sign Up" to create a new account
3. Enter your email and password
4. Login with your credentials

### 2. Creating a Project

1. From the dashboard, click "New Project"
2. Enter a project name
3. Click "Create"

### 3. Adding Criteria

1. In your project, click "Add Criterion"
2. Enter criterion name (e.g., "Price", "Quality")
3. Select criterion type:
   - **Benefit**: Higher values are better (e.g., Quality, Performance)
   - **Cost**: Lower values are better (e.g., Price, Time)
4. Set the weight (importance) of the criterion
5. Click "Add"

### 4. Adding Alternatives

1. Click "Add Alternative"
2. Enter alternative name (e.g., "Option A", "Product 1")
3. Enter values for each criterion
4. Click "Add"

### 5. Running TOPSIS Calculation

1. Ensure you have at least one criterion and one alternative
2. Click "Calculate TOPSIS"
3. View the results with ranking and detailed calculations

### 6. CSV Import

1. From the dashboard, click "Import CSV"
2. Choose a CSV file with your data
3. Preview the data and set project name
4. Click "Import"

**CSV Format Example:**
```csv
Alternative,Price,Quality,Performance
Option A,100,8,7
Option B,150,9,8
Option C,80,6,6
```

## API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login

### Projects
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details

### Criteria
- `POST /api/projects/{id}/criteria` - Add criterion to project

### Alternatives
- `POST /api/projects/{id}/alternatives` - Add alternative to project

### Calculations
- `POST /api/projects/{id}/calculate` - Run TOPSIS calculation

### File Operations
- `POST /api/upload-csv` - Upload CSV file
- `POST /api/import-csv` - Import CSV data

## TOPSIS Method Overview

The TOPSIS method follows these steps:

1. **Normalization**: Convert raw values to normalized values
2. **Weighting**: Apply criterion weights to normalized values
3. **Ideal Solutions**: Determine positive and negative ideal solutions
4. **Distance Calculation**: Calculate distances to ideal solutions
5. **Preference Values**: Compute final preference values
6. **Ranking**: Rank alternatives based on preference values

## Project Structure

```
DecisionSupportSystem/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── TOPSIS.PY             # Original TOPSIS logic
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── contexts/     # React contexts (Auth, Theme)
│   │   ├── pages/        # Application pages
│   │   └── App.tsx       # Main application component
│   ├── package.json      # Node.js dependencies
│   └── README.md         # Frontend documentation
└── README.md             # This file
```

## Development

### Backend Development

```bash
# Run in development mode with auto-reload
python app.py
```

### Frontend Development

```bash
cd frontend
npm start
```

### Database

The application uses SQLite by default. For production, consider using PostgreSQL or MySQL by setting the `DATABASE_URL` environment variable.

## Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///topsis.db
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `app.py` or kill the process using the port
2. **CORS errors**: Ensure the backend is running on port 5000
3. **Database errors**: Delete the `topsis.db` file and restart the application
4. **Node modules issues**: Delete `node_modules` and run `npm install` again

### Logs

- Backend logs are displayed in the terminal where you run `python app.py`
- Frontend logs are available in the browser's developer console

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository. 
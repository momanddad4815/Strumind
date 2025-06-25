# StruMind - Next-Generation Structural Engineering Platform

StruMind is a comprehensive, AI-powered, cloud-native structural engineering platform that combines and replaces ETABS, Tekla Structures, and STAAD.Pro into one unified system.

## 🏗️ Architecture Overview

### Backend Engine (Python + FastAPI)
- **Core Modeling Engine**: Complete structural modeling with nodes, elements, materials, sections, loads
- **Solver Engine**: Linear/nonlinear static, modal, response spectrum, time history analysis
- **Design Engine**: RC, Steel, Composite design per international codes (IS 456, ACI 318, AISC 360, etc.)
- **Detailing Engine**: Automated reinforcement and steel detailing with bar schedules
- **BIM Integration**: Full IFC 4.x, glTF, DXF import/export capabilities
- **RESTful APIs**: Comprehensive APIs with JWT authentication and multi-tenant support

### Frontend SaaS Application (Next.js + React)
- **Modern SaaS Interface**: Multi-tenant organization and project management
- **3D Modeling Interface**: Interactive structural modeling with snapping and real-time updates
- **Analysis & Design Execution**: Real-time analysis execution and result visualization
- **3D BIM Viewer**: React Three Fiber-based 3D visualization with camera controls
- **Real-time Collaboration**: Multi-user editing and project sharing

### Database (PostgreSQL)
- **Complete Schema**: Users, organizations, projects, models, analysis results
- **Multi-tenant Architecture**: Secure data isolation per organization
- **Full Relationships**: Foreign keys, indexing, and data integrity constraints

## 🚀 Key Features

### Analysis Capabilities
- ✅ Linear static analysis with P-Delta effects
- ✅ Modal analysis with eigenvalue extraction
- ✅ Response spectrum analysis with CQC combination
- ✅ Nonlinear static analysis capabilities
- ✅ Dynamic analysis (modal, response spectrum, time history)
- ✅ Load combinations per international codes

### Design Engines
- 🔄 RC Design (IS 456, ACI 318, Eurocode 2) - In Progress
- 🔄 Steel Design (IS 800, AISC 360, Eurocode 3) - In Progress
- 🔄 Composite design capabilities - In Progress
- 🔄 Foundation design - In Progress
- 🔄 Seismic design checks - In Progress

### BIM & Interoperability
- 🔄 IFC 4.x export/import - In Progress
- 🔄 glTF export for web visualization - In Progress
- 🔄 DXF export for CAD integration - In Progress
- 🔄 Full 3D BIM model generation - In Progress

### Advanced Features
- ✅ Material and section libraries (International standards)
- ✅ Automated load generation (wind, seismic per codes)
- ✅ Boundary conditions and releases
- ✅ Multi-tenant SaaS architecture
- ✅ JWT-based authentication
- ✅ Real-time model validation

## 🛠️ Technology Stack

### Backend
- **Python 3.12+** - Scientific computing and analysis
- **FastAPI** - High-performance web framework
- **SQLAlchemy** - ORM for database interactions
- **PostgreSQL** - Primary database
- **NumPy/SciPy** - Numerical computations
- **Celery + Redis** - Background task processing

### Frontend
- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type-safe development
- **TailwindCSS + ShadCN UI** - Modern styling
- **React Three Fiber + Drei** - 3D visualization
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management

### Infrastructure
- **Docker** - Containerization
- **PostgreSQL** - Database
- **Redis** - Caching and task queue
- **Cloud deployment ready**

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional, for background tasks)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Configure database
export DATABASE_URL="postgresql://username:password@localhost:5432/strumind"

# Run development server
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install

# Configure API endpoint
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

### Database Setup
```sql
-- Create database
CREATE DATABASE strumind;

-- The application will automatically create tables on first run
```

## 📚 API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/token` - User login
- `GET /auth/me` - Current user info

#### Projects & Models
- `GET /projects/` - List projects
- `POST /projects/` - Create project
- `GET /models/{model_id}/data` - Get model data
- `POST /models/{model_id}/simple-frame` - Create simple frame
- `POST /models/{model_id}/simple-building` - Create simple building

#### Analysis
- `POST /analysis/{model_id}/linear-static` - Run linear static analysis
- `POST /analysis/{model_id}/modal` - Run modal analysis
- `POST /analysis/{model_id}/response-spectrum` - Run response spectrum analysis
- `GET /analysis/{model_id}/results` - Get analysis results

## 🏗️ Structural Engineering Features

### Modeling Capabilities
- **Elements**: Beams, columns, braces, shells, plates, walls, slabs
- **Materials**: Concrete, steel, timber, composite with international standards
- **Sections**: I-sections, channels, tubes, custom sections with property libraries
- **Loads**: Point, distributed, area, wind (automated), seismic (code-based)
- **Boundary Conditions**: Fixed, pinned, roller, spring supports
- **Releases**: Moment and force releases at element ends

### Analysis Features
- **Linear Static**: Full 3D frame analysis with P-Delta effects
- **Modal Analysis**: Eigenvalue extraction with mass normalization
- **Response Spectrum**: Seismic analysis with CQC/SRSS combination
- **Load Combinations**: Automated generation per design codes
- **Result Processing**: Displacements, forces, stresses, reactions

### Design Codes Support
- **Concrete**: IS 456, ACI 318, Eurocode 2
- **Steel**: IS 800, AISC 360, Eurocode 3
- **Seismic**: IS 1893, ASCE 7
- **Wind**: IS 875, ASCE 7
- **Load Combinations**: Per respective design codes

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- Python: Follow PEP 8, use type hints
- TypeScript: Strict mode, proper typing
- Testing: Comprehensive test coverage
- Documentation: Clear docstrings and comments

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](https://docs.strumind.com)
- 🐛 [Issue Tracker](https://github.com/strumind/strumind/issues)
- 💬 [Community Forum](https://community.strumind.com)
- 📧 [Email Support](mailto:support@strumind.com)

## 🗺️ Roadmap

### Phase 1 (Completed)
- ✅ Core modeling engine
- ✅ Linear static analysis
- ✅ Modal analysis
- ✅ Basic SaaS frontend
- ✅ API layer with authentication

### Phase 2 (In Progress)
- 🔄 Design engines (RC, Steel)
- 🔄 BIM integration (IFC, glTF)
- 🔄 Advanced 3D visualization
- 🔄 Detailing engine

### Phase 3 (Planned)
- 📋 Nonlinear analysis
- 📋 AI-powered optimization
- 📋 Mobile applications
- 📋 Advanced collaboration tools
- 📋 Reporting and documentation

---

**StruMind** - Revolutionizing structural engineering through AI and cloud technology.

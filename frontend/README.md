# Pupper Frontend

A React application for the Pupper dog adoption platform, allowing users to browse, search, and interact with Labrador Retrievers available for adoption.

## Features

### 🐕 Dog Browsing
- **Grid View**: Beautiful card-based layout showing dog thumbnails
- **Detailed View**: Comprehensive dog profiles with full information
- **Image Gallery**: Click thumbnails to view original high-resolution images
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices

### 🔍 Search & Filtering
- **Advanced Search**: Filter by state, weight, age, and color
- **Real-time Results**: Instant search with debounced input
- **Active Filters**: Visual indicators of applied filters
- **Clear Filters**: Easy reset of all search criteria

### ❤️ Favorites System
- **Save Dogs**: Heart icon to add/remove favorites
- **Persistent Storage**: Favorites saved in localStorage
- **Dedicated Page**: View all favorite dogs in one place
- **Statistics**: Track your favorite dog statistics

### 🗳️ Voting System
- **Wag/Growl**: Vote on dogs with thumbs up/down
- **Real-time Updates**: Instant vote count updates
- **Visual Feedback**: Animated voting buttons
- **Community Engagement**: See how others have voted

### 🖼️ Image Features
- **Thumbnail Display**: Optimized 400x400 images for fast loading
- **Original Images**: Click to view full-resolution photos
- **Image Modal**: Full-screen image viewer with zoom and rotate
- **Multiple Sizes**: Automatic fallback to available image sizes
- **Loading States**: Skeleton loading and error handling

## Technology Stack

### Core Technologies
- **React 18**: Modern React with hooks and functional components
- **React Router**: Client-side routing for SPA navigation
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Axios**: HTTP client for API communication

### State Management & Data Fetching
- **React Query**: Server state management with caching
- **Custom Hooks**: Reusable logic for dogs, favorites, and voting
- **Local Storage**: Client-side persistence for favorites

### UI Components & Styling
- **Lucide React**: Beautiful SVG icons
- **React Modal**: Accessible modal dialogs
- **React Toastify**: Toast notifications for user feedback
- **Loading Skeletons**: Smooth loading states

### Development Tools
- **Create React App**: Build tooling and development server
- **PostCSS**: CSS processing with Tailwind
- **ESLint**: Code linting and formatting

## Project Structure

```
frontend/
├── public/
│   ├── index.html          # Main HTML template
│   ├── manifest.json       # PWA manifest
│   └── favicon.ico         # App icon
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Header.js       # Navigation header
│   │   ├── Footer.js       # Site footer
│   │   ├── DogCard.js      # Dog thumbnail card
│   │   ├── ImageModal.js   # Full-screen image viewer
│   │   └── LoadingSkeleton.js # Loading placeholders
│   ├── pages/              # Route components
│   │   ├── HomePage.js     # Main dog browsing page
│   │   ├── DogDetailsPage.js # Individual dog details
│   │   ├── SearchPage.js   # Advanced search interface
│   │   ├── FavoritesPage.js # User's favorite dogs
│   │   └── NotFoundPage.js # 404 error page
│   ├── hooks/              # Custom React hooks
│   │   └── useDogs.js      # Dog data management hooks
│   ├── services/           # API and utility services
│   │   └── api.js          # API client and utilities
│   ├── App.js              # Main app component
│   ├── App.css             # Global styles and utilities
│   └── index.js            # React app entry point
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
└── postcss.config.js       # PostCSS configuration
```

## Getting Started

### Prerequisites
- Node.js 16+ and npm
- Backend API running (see backend README)

### Installation

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Configuration**
   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:3001/api
   ```

3. **Start Development Server**
   ```bash
   npm start
   ```
   
   The app will open at `http://localhost:3000`

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

## API Integration

### REST API Endpoints
The frontend integrates with the following backend endpoints:

- `GET /dogs` - Fetch dogs with optional filters
- `GET /dogs/:id` - Fetch single dog details
- `POST /dogs/:id/vote` - Vote on a dog
- `GET /images/:id` - Fetch image metadata

### Data Flow
1. **React Query** manages server state and caching
2. **Custom hooks** provide clean API interfaces
3. **Optimistic updates** for voting and favorites
4. **Error handling** with user-friendly messages

## Key Features Implementation

### Image Handling
```javascript
// Automatic image size selection with fallbacks
const thumbnailUrl = apiUtils.getImageUrl(dog, '400x400');
const originalUrl = apiUtils.getImageUrl(dog, 'original');

// Click to view full-size image
<img 
  src={thumbnailUrl}
  onClick={() => handleImageClick('original')}
  className="cursor-pointer hover:scale-105"
/>
```

### Responsive Design
```css
/* Mobile-first responsive grid */
.dog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 640px) {
  .dog-grid {
    grid-template-columns: 1fr;
  }
}
```

### State Management
```javascript
// React Query for server state
const { data, isLoading, error } = useDogs(filters);

// Local state for UI interactions
const [showImageModal, setShowImageModal] = useState(false);

// Custom hooks for complex logic
const { isFavorite, toggleFavorite } = useFavorites();
```

## Performance Optimizations

### Image Loading
- **Lazy Loading**: Images load only when visible
- **Skeleton Loading**: Smooth loading states
- **Error Handling**: Graceful fallbacks for broken images
- **Size Optimization**: Automatic selection of appropriate image sizes

### Data Fetching
- **React Query Caching**: Intelligent server state caching
- **Debounced Search**: Reduced API calls during typing
- **Optimistic Updates**: Immediate UI feedback for votes
- **Background Refetching**: Keep data fresh automatically

### Bundle Optimization
- **Code Splitting**: Route-based code splitting with React Router
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Optimized images and fonts
- **Gzip Compression**: Reduced bundle sizes

## User Experience Features

### Accessibility
- **Semantic HTML**: Proper heading hierarchy and landmarks
- **ARIA Labels**: Screen reader friendly interactions
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Management**: Proper focus handling in modals

### Progressive Enhancement
- **Offline Capability**: Service worker for basic offline functionality
- **PWA Features**: Installable web app with manifest
- **Responsive Images**: Optimized for different screen densities
- **Touch Interactions**: Mobile-friendly touch targets

### Visual Design
- **Consistent Branding**: Cohesive color scheme and typography
- **Smooth Animations**: CSS transitions and micro-interactions
- **Loading States**: Skeleton screens and spinners
- **Error States**: Friendly error messages and recovery options

## Deployment

### Production Build
```bash
npm run build
```

### Environment Variables
```env
REACT_APP_API_URL=https://api.pupper-app.com
REACT_APP_ENVIRONMENT=production
```

### Hosting Options
- **Netlify**: Automatic deployments from Git
- **Vercel**: Optimized for React applications
- **AWS S3 + CloudFront**: Scalable static hosting
- **GitHub Pages**: Free hosting for open source projects

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Browsers**: iOS Safari 14+, Chrome Mobile 90+
- **Progressive Enhancement**: Graceful degradation for older browsers

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for new components (migration in progress)
3. Write tests for new functionality
4. Ensure responsive design works on all screen sizes
5. Test with screen readers for accessibility

## Future Enhancements

### Planned Features
- **User Authentication**: Login and user profiles
- **Advanced Filtering**: More sophisticated search options
- **Dog Matching**: AI-powered dog recommendations
- **Adoption Process**: Integrated adoption workflow
- **Real-time Updates**: WebSocket integration for live updates

### Technical Improvements
- **TypeScript Migration**: Gradual migration to TypeScript
- **Testing Suite**: Comprehensive unit and integration tests
- **Performance Monitoring**: Real user monitoring and analytics
- **Internationalization**: Multi-language support

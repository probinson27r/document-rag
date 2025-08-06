# Canny.io Feedback Integration Guide

This guide explains how to set up and use the Canny.io feedback integration in the ED19024 application.

## Overview

The feedback system allows users to submit feedback directly to Canny.io from the chat interface. Users can click the feedback button in the bottom-left corner to open a modal where they can enter their feedback, which will be automatically submitted to your Canny.io board.

## Setup Instructions

### 1. Get Your Canny.io API Key

1. Log in to your Canny.io account
2. Go to **Settings** → **API**
3. Copy your **Secret API Key**
4. Keep this key secure and never share it publicly

### 2. Get Your Board ID

1. In your Canny.io dashboard, navigate to the board where you want feedback to be posted
2. The board ID is in the URL: `https://your-company.canny.io/admin/board/[BOARD_ID]`
3. Copy the board ID

### 3. Configure Environment Variables

Add the following environment variables to your `.env.local` file (or set them in your deployment environment):

```bash
CANNY_API_KEY=your_secret_api_key_here
CANNY_BOARD_ID=your_board_id_here
```

### 4. Local Development

For local development, you can set these variables in your shell:

```bash
export CANNY_API_KEY="your_secret_api_key_here"
export CANNY_BOARD_ID="your_board_id_here"
```

### 5. AWS Deployment

For AWS deployment, add these environment variables to your ECS task definition or set them in the deployment script.

## Features

### Feedback Button
- Located in the bottom-left corner of the chat interface
- Styled with a blue background and chat bubble icon
- Hover effects for better user experience

### Feedback Modal
- Clean, modern design matching the application's style
- Form fields for title and detailed feedback
- Responsive design that works on all screen sizes
- Keyboard shortcuts (Escape to close)
- Click outside to close functionality

### User Information
- Automatically captures user email and name from the session
- Falls back to anonymous user if session data is not available
- Submits feedback with proper attribution

### Error Handling
- Comprehensive error handling for API failures
- User-friendly error messages
- Loading states during submission
- Success notifications

## API Endpoint

The feedback system uses the following endpoint:

- **URL**: `/api/feedback`
- **Method**: `POST`
- **Authentication**: Required (uses existing auth system)
- **Content-Type**: `application/json`

### Request Body
```json
{
  "title": "Brief description of feedback",
  "details": "Detailed feedback content"
}
```

### Response
```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "post_id": "canny_post_id"
}
```

## Canny.io API Integration

The system integrates with Canny.io's API to create posts:

- **Endpoint**: `https://canny.io/api/v1/posts/create`
- **Method**: `POST`
- **Authentication**: Uses your secret API key
- **Board**: Posts to your specified board

### Canny User Creation
The system first creates or updates the user in Canny:

```json
{
  "apiKey": "your_api_key",
  "email": "user@example.com",
  "name": "User Name"
}
```

### Canny Post Data
```json
{
  "apiKey": "your_api_key",
  "boardID": "your_board_id",
  "title": "User's feedback title",
  "details": "User's detailed feedback",
  "authorID": "canny_user_id"
}
```

## Troubleshooting

### Common Issues

1. **"Canny API key not configured"**
   - Ensure `CANNY_API_KEY` is set in your environment variables
   - Check that the variable name is correct

2. **"Canny board ID not configured"**
   - Ensure `CANNY_BOARD_ID` is set in your environment variables
   - Verify the board ID is correct

3. **"Failed to submit feedback"**
   - Check your Canny.io API key is valid
   - Verify the board ID exists and is accessible
   - Check network connectivity to Canny.io

4. **Authentication errors**
   - Ensure the user is properly authenticated
   - Check that the session contains user information

5. **"invalid author id" errors**
   - This occurs when the user creation step fails
   - Check that the user email and name are valid
   - Verify the Canny API key has permissions to create users
   - Check the application logs for user creation errors

### Debugging

Enable debug logging by checking the application logs for:
- API request/response details
- User session information
- Error messages from Canny.io

## Security Considerations

1. **API Key Security**
   - Never expose your Canny API key in client-side code
   - Use environment variables for configuration
   - Rotate API keys regularly

2. **User Data**
   - Only collect necessary user information
   - Respect user privacy preferences
   - Handle anonymous feedback appropriately

3. **Rate Limiting**
   - Consider implementing rate limiting for feedback submissions
   - Monitor API usage to avoid hitting Canny.io limits

## Customization

### Styling
The feedback button and modal can be customized by modifying the CSS in `templates/claude_style_interface.html`:

- `.feedback-button` - Main feedback button styles
- `.feedback-modal` - Modal container styles
- `.feedback-form` - Form styling

### Functionality
The feedback submission logic can be modified in the JavaScript section of the template:

- `submitFeedback()` function - Handles form submission
- `openFeedbackModal()` and `closeFeedbackModal()` - Modal controls

## Support

For issues with:
- **Canny.io API**: Contact Canny.io support
- **Application Integration**: Check the application logs and this guide
- **Deployment**: Refer to the AWS deployment documentation

## References

- [Canny.io API Documentation](https://developers.canny.io/api-reference)
- [Canny.io Post Creation API](https://developers.canny.io/api-reference#create-post)
- [Flask Application Documentation](README.md) 
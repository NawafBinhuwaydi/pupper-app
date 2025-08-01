import { Amplify } from 'aws-amplify';

const awsConfig = {
  Auth: {
    Cognito: {
      userPoolId: 'us-east-1_a2CLhjpIC',
      userPoolClientId: '39cae69n5ouec652bltvvn1t94',
      loginWith: {
        username: true,
        email: true
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: {
          required: true
        }
      },
      allowGuestAccess: false,
      passwordFormat: {
        minLength: 6,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: false
      }
    }
  },
  API: {
    REST: {
      PupperApi: {
        endpoint: process.env.REACT_APP_API_URL || 'https://bj9jbp1rgf.execute-api.us-east-1.amazonaws.com/prod',
        region: 'us-east-1'
      }
    }
  }
};

Amplify.configure(awsConfig);

export default awsConfig;

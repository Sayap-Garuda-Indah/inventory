import type { Configuration, PopupRequest } from '@azure/msal-browser'
// import type { redirect } from 'react-router-dom';

console.log('Initializing MSAL configuration');
console.log('Environment Variables:', {
    client_id: import.meta.env.VITE_MSAL_CLIENT_ID,
    tenan_id: import.meta.env.VITE_MSAL_TENANT_ID,
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_MSAL_TENANT_ID}`,
    redirectUrl: import.meta.env.VITE_MSAL_REDIRECT_URI,
    apiBaseUrl: import.meta.env.VITE_API_BASE_UR
});

// Validate required environment variables
if (!import.meta.env.VITE_MSAL_CLIENT_ID) {
    console.error('❌ VITE_MSAL_CLIENT_ID is not set!');
}
if (!import.meta.env.VITE_MSAL_TENANT_ID) {
    console.error('❌ VITE_MSAL_TENANT_ID is not set!');
}
if (!import.meta.env.VITE_API_BASE_URL) {
    console.error('❌ VITE_API_BASE_URL is not set! API calls will fail.');
}

export const msalConfig: Configuration = {
    auth: {
        clientId: import.meta.env.VITE_MSAL_CLIENT_ID,
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_MSAL_TENANT_ID}`,
        redirectUri: import.meta.env.VITE_MSAL_REDIRECT_URI || 'http://localhost:5173',
        navigateToLoginRequestUrl: false,   // Prevent redirect loop
    },
    cache: {
        cacheLocation: 'sessionStorage', // This configures where your cache will be stored
        storeAuthStateInCookie: false, // Set this to "true" if you are having issues on IE11 or Edge
    },
    system: {
        loggerOptions: {
            loggerCallback: (level, message, containsPii) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case 0: // Error
                        console.error('[MSAL Error]:', message);
                        break;
                    case 1: // Warning
                        console.warn('[MSAL Warning]:', message);
                        break;
                    case 2: // Info
                        console.info('[MSAL Info]:', message);
                        break;
                    case 3: // Verbose
                        console.debug('[MSAL Verbose]:', message);
                        break;
                }
            },
            logLevel: 3, // Set the log level to Verbose
            piiLoggingEnabled: false,
        },
    },

};

console.log('MSAL Config Created:', {
    clientId: msalConfig.auth.clientId,
    authority: msalConfig.auth.authority,
    redirectUri: msalConfig.auth.redirectUri
});

export const loginRequest: PopupRequest = {
    scopes: [`api://${import.meta.env.VITE_MSAL_CLIENT_ID}/access_as_user`]
};

console.log('Login request scopes:', loginRequest.scopes);
console.log('MSAL Configuration Loaded Successfully');
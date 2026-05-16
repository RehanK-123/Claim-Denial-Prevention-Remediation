const awsConfig = {
  Auth: {
    Cognito: {
      userPoolId: "us-east-1_zSTxe2BWO",
      userPoolClientId: "4n9rrc9o53vjng827bvdhrlvdh",
      loginWith: {
        oauth: {
          domain: "us-east-1zstxe2bwo.auth.us-east-1.amazoncognito.com",
          scopes: ["email", "openid", "phone"],
          redirectSignIn: ["http://localhost:5173/"],
          redirectSignOut: ["http://localhost:5173/"],
          responseType: "code",
        },
      },
    },
  },
};

export default awsConfig;


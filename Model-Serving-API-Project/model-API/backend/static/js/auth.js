const domain = "dev-co6yb05mykgajw4l.us.auth0.com";
const client_id = "zE5EKklGzJgwuAt6D5JFfKWhYyvSvaj6";
const audience = "https://api.cryptonest.io";
const scope = "models:list predictions:create predictions:read models:read";

let auth0Client = null;
let accessToken = null;

async function initAuth() {
  auth0Client = await createAuth0Client({ domain, client_id, audience, scope });

  if (await auth0Client.isAuthenticated()) {
    accessToken = await auth0Client.getTokenSilently();
    return true;
  }

  return false;
}

async function login() {
  await auth0Client.loginWithPopup({
    authorizationParams: { audience, scope }
  });
  accessToken = await auth0Client.getTokenSilently();
}

function logout() {
  auth0Client.logout({ logoutParams: { returnTo: window.location.origin } });
}

function getToken() {
  return accessToken;
}

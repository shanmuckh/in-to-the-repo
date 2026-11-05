export const host = process.env.NEXT_PUBLIC_HOST || "http://127.0.0.1:8000";
export const repoAnalysisRoute = `${host}/api/analyze`
export const fileAnalysisRoute = `${host}/api/file`
export const askAssistantRoute = `${host}/api/ask`
export const repoVerifyRoute = `${host}/api/verify`
export const getAnalysisByIdRoute = (id: number) => `${host}/api/analysis/${id}`
export const signupRoute = `${host}/api/auth/signup`
export const loginRoute = `${host}/api/auth/login`
export const userMeRoute = `${host}/api/auth/me`
export const userHistoryRoute = `${host}/api/user/history`
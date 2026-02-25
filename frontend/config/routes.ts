const INDEX_API_ROUTE = process.env.BACKEND_URL;

const API_ROUTES = {
    base: INDEX_API_ROUTE,
    healthcheck: `${INDEX_API_ROUTE}/healthcheck`,
};

type ApiRoutes = typeof API_ROUTES;

export {API_ROUTES};
export type {ApiRoutes};

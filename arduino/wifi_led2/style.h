const char STYLE_CSS[] = R"rawliteral(
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    margin: 0;
    padding: 2rem;
    background-color: #f8f9fa;
    color: #212529;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    text-align: center;
}
.container {
    background-color: #ffffff;
    padding: 2rem 3rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    max-width: 400px;
    width: 100%;
}
h1 {
    color: #343a40;
    margin-bottom: 1.5rem;
}
.status {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    padding: 0.75rem;
    border-radius: 0.25rem;
}
.status.on {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
.status.off {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}
.buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
}
.btn {
    display: inline-block;
    font-weight: 400;
    color: #fff;
    text-align: center;
    vertical-align: middle;
    cursor: pointer;
    user-select: none;
    background-color: #007bff;
    border: 1px solid #007bff;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    line-height: 1.5;
    border-radius: 0.25rem;
    text-decoration: none;
    transition: all 0.15s ease-in-out;
}
.btn-on {
    background-color: #28a745;
    border-color: #28a745;
}
.btn-on:hover {
    background-color: #218838;
    border-color: #1e7e34;
}
.btn-off {
    background-color: #dc3545;
    border-color: #dc3545;
}
.btn-off:hover {
    background-color: #c82333;
    border-color: #bd2130;
}
)rawliteral";

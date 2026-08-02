const KEY = "news-theme";
const root = document.documentElement;
const saved = localStorage.getItem(KEY);
if (saved) root.dataset.theme = saved;
document.getElementById("theme-toggle").addEventListener("click", () => {
  const dark = root.dataset.theme === "dark" ||
    (!root.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  root.dataset.theme = dark ? "light" : "dark";
  localStorage.setItem(KEY, root.dataset.theme);
});

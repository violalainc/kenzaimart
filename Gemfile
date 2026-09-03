source "https://rubygems.org"

# GitHub Pages が公式サポートしているバージョン一式（Jekyll本体や各種プラグインを含む）
gem "github-pages", group: :jekyll_plugins

group :jekyll_plugins do
  gem "jekyll-seo-tag"
  gem "jekyll-sitemap"
end

# Windows / JRuby環境での文字コード関連の問題を避けるため
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

gem "wdm", "~> 0.1.1", :platforms => [:mingw, :x64_mingw, :mswin]

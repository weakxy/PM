module.exports = {
  "sourceType": "unambiguous",
  "presets": [
    ["@babel/preset-env",
      {
        "targets": {
          "browsers": ["> 1%", "last 2 versions"]
        }
      }
    ]
  ],
  "plugins": [
    "@babel/plugin-transform-runtime"
  ]
}
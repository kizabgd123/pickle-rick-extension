{
  inputs = {
    garnix-lib.url = "github:garnix-io/garnix-lib";
    Haskell.url = "github:garnix-io/haskell-module";
    NodeJS.url = "github:garnix-io/nodejs-module";
    PostgreSQL.url = "github:garnix-io/postgresql-module";
    Rust.url = "github:garnix-io/rust-module";
    UptimeKuma.url = "github:garnix-io/uptime-kuma-module";
    User.url = "github:garnix-io/user-module";
  };

  nixConfig = {
    extra-substituters = [ "https://cache.garnix.io" ];
    extra-trusted-public-keys = [ "cache.garnix.io:CTFPyKSLcx5RMJKfLo5EEPUObbA78b0YQ2DTCJXqr9g=" ];
  };

  outputs = inputs: inputs.garnix-lib.lib.mkModules {
    modules = [
      inputs.Haskell.garnixModules.default
      inputs.NodeJS.garnixModules.default
      inputs.PostgreSQL.garnixModules.default
      inputs.Rust.garnixModules.default
      inputs.UptimeKuma.garnixModules.default
      inputs.User.garnixModules.default
    ];

    config = { pkgs, ... }: {
      haskell = {
        haskell-project = {
          buildDependencies = [  ];
          devTools = [  ];
          ghcVersion = "9.8";
          runtimeDependencies = [  ];
          src = ./.;
          webServer = null;
        };
      };
      nodejs = {
        nodejs-project = {
          buildDependencies = [  ];
          devTools = [  ];
          prettier = false;
          runtimeDependencies = [  ];
          src = ./.;
          testCommand = "npm run test";
          webServer = null;
        };
      };
      postgresql = {
        postgresql-project = {
          port = 5432;
        };
      };
      rust = {
        rust-project = {
          buildDependencies = [  ];
          devTools = [  ];
          runtimeDependencies = [  ];
          src = ./.;
          webServer = null;
        };
      };
      uptimeKuma = {
        uptimeKuma-project = {
          path = "/";
          port = 3001;
        };
      };
      user = {
        user-project = {
          authorizedSshKeys = [  ];
          groups = [  ];
          shell = "bash";
          user = "kiza123";
        };
      };

      garnix.deployBranch = "main";
    };
  };
}

import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";

export class DockerLambdaAwsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const forecast_dockerFunc = new lambda.DockerImageFunction(this, "Forecast_DockerFunc", {
      code: lambda.DockerImageCode.fromImageAsset("./forecast_image"),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(600),
      functionName: "foodsight-latest-grasscast-forecast-data",
    });

    const climate_dockerFunc = new lambda.DockerImageFunction(this, "Climate_DockerFunc", {
      code: lambda.DockerImageCode.fromImageAsset("./climate_image"),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(600),
      functionName: "foodsight-latest-noaa-climate-data",
    });

  }
}

// cdk bootstrap
// cdk deploy

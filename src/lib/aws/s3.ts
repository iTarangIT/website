import {
  S3Client,
  GetObjectCommand,
  ListObjectsV2Command,
} from "@aws-sdk/client-s3";

function getS3Client(): S3Client {
  const region = process.env.AWS_REGION;
  const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
  const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;

  if (!region || !accessKeyId || !secretAccessKey) {
    throw new Error(
      "[S3] Missing AWS credentials. Set AWS_REGION, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY in .env.local"
    );
  }

  return new S3Client({
    region,
    credentials: { accessKeyId, secretAccessKey },
  });
}

/**
 * Download a file from S3 and return it as a Buffer.
 */
export async function fetchFileFromS3(key: string): Promise<Buffer> {
  const client = getS3Client();
  const bucket = process.env.AWS_S3_BUCKET;
  if (!bucket) throw new Error("[S3] Missing AWS_S3_BUCKET in .env.local");

  const command = new GetObjectCommand({ Bucket: bucket, Key: key });
  const response = await client.send(command);

  if (!response.Body) {
    throw new Error(`[S3] Empty response body for key: ${key}`);
  }

  // Convert readable stream to Buffer
  const chunks: Uint8Array[] = [];
  const stream = response.Body as AsyncIterable<Uint8Array>;
  for await (const chunk of stream) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

/**
 * List all file keys in the bucket (optionally under a prefix).
 */
export async function listS3Files(prefix?: string): Promise<string[]> {
  const client = getS3Client();
  const bucket = process.env.AWS_S3_BUCKET;
  if (!bucket) throw new Error("[S3] Missing AWS_S3_BUCKET in .env.local");

  const command = new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix });
  const response = await client.send(command);

  return (response.Contents ?? [])
    .map((obj) => obj.Key)
    .filter((key): key is string => !!key);
}

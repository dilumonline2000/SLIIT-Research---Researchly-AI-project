import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProfilePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Profile</h1>
      <Card>
        <CardHeader>
          <CardTitle>Personal details</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Profile editor — implementation pending Phase 4.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

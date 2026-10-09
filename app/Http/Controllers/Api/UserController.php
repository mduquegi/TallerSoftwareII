<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\BulkStoreUsersRequest;
use App\Http\Requests\UserListRequest;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function index(UserListRequest $request): JsonResponse
    {
        return response()->json(
            User::query()->orderBy('id')->paginate($request->perPage())
        );
    }

    public function emails(UserListRequest $request): JsonResponse
    {
        return response()->json(
            User::query()
                ->select(['id', 'email'])
                ->orderBy('id')
                ->paginate($request->perPage())
        );
    }

    public function overTwenty(UserListRequest $request): JsonResponse
    {
        $cutoff = Carbon::now()->subYears(20)->startOfDay();

        $users = User::query()
            ->where('birth_date', '<=', $cutoff->toDateString())
            ->orderBy('id')
            ->paginate($request->perPage());

        return response()->json([
            'cutoff_date' => $cutoff->toDateString(),
            'users' => $users,
        ]);
    }

    public function bulkStore(BulkStoreUsersRequest $request): JsonResponse
    {
        $created = [];

        foreach ($request->validated()['users'] as $userData) {
            $created[] = User::create([
                'name' => $userData['name'],
                'email' => $userData['email'],
                'birth_date' => $userData['birth_date'],
                'password' => Hash::make($userData['password'] ?? 'password'),
            ]);
        }

        return response()->json([
            'message' => 'Se crearon 3 usuarios correctamente.',
            'users' => $created,
        ], 201);
    }
}
